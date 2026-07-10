"""
=============================================================================
 SCORING ENGINE — le CŒUR du système SkillMatch AI
-----------------------------------------------------------------------------
 Rôle : à partir d'un CV (cv_data) et d'une exigence de poste (req_data),
 produire un SCORE GLOBAL sur 100 + une décision (Excellent/Fort/Modéré/Faible).

 PIPELINE DE CALCUL (fonction compute_scoring) :

   1) BUSINESS CONTEXT RESOLVER : on détecte la "famille de poste" depuis
      l'offre (coach, ingénieur, RH...) et on charge des PONDÉRATIONS adaptées.
      -> un même CV n'est pas jugé pareil pour un poste technique ou pédagogique.

   2) CALCUL DES 6 CRITÈRES (chacun donne un ratio 0..1) :
        spécialité, compétences techniques, expérience, pédagogie,
        soft skills, similarité sémantique.
      Chaque ratio est multiplié par le POIDS du critère -> note pondérée.

   3) GATE DE COMPATIBILITÉ DE DOMAINE : si le CV et l'offre relèvent de
      domaines différents (ex : CV agricole vs poste IT), on écrase le score
      (multiplicateur faible) et on lève un drapeau "hors domaine".

   4) SCORE FINAL = somme des notes pondérées × multiplicateur de domaine,
      plafonné si le profil est hors périmètre.

 Le résultat est un dictionnaire riche (score, décision, détail par critère,
 contexte métier détecté...) consommé par l'API puis l'interface.
=============================================================================
"""
from __future__ import annotations

from src.config import SCORING_WEIGHTS, SHORTLIST_THRESHOLDS
from src.constants import DECISION_LABELS, RECOMMENDATION_LABELS
from src.scoring.embeddings import (
    build_cv_semantic_text,
    build_requirement_semantic_text,
    compute_semantic_similarity,
)
from src.scoring.business_context_resolver import (
    resolve_business_context,
    family_keyword_ratio,
    detect_family_from_text,
    detect_domains_from_text,
)
from src.scoring.business_ontology import domain_of, detect_external_domain
from src.scoring.experience_levels import EXPERIENCE_LEVELS
from src.scoring.experience_matcher import compute_experience_match
from src.scoring.education_matcher import compute_education_score
from src.scoring.pedagogy_matcher import compute_pedagogy_match
from src.scoring.skill_matcher import compute_skill_match
from src.scoring.soft_skills_matcher import compute_soft_skill_match
from src.scoring.speciality_detector import detect_speciality_from_cv, detect_speciality_from_requirement


import re
from src.scoring.synonyms import term_in_text

# Mots servant à DÉTECTER si un critère est mentionné dans l'exigence
# (en complément des champs parsés par le LLM — fiabilité accrue).
_SOFT_DETECT = [
    "communication", "équipe", "equipe", "team", "teamwork", "collaboration",
    "leadership", "autonomie", "autonome", "créativité", "creativite", "rigueur",
    "adaptabilité", "adaptabilite", "organisation", "proactif", "proactivité",
    "empathie", "relationnel", "soft skills", "savoir-être",
]
_PEDAGOGY_DETECT = [
    "pédagogie", "pedagogie", "enseignement", "enseignant", "formateur",
    "tutorat", "tuteur", "mentorat", "encadrement", "animation", "animateur",
    "coach", "coaching", "elearning", "e-learning", "scratch",
]
_EXP_RE = re.compile(r"\d+\s*(?:an|ans|année|années|year|years)", re.IGNORECASE)


def _has_level_signal(text: str) -> bool:
    lowered = (text or "").lower()
    if _EXP_RE.search(lowered):
        return True
    return any(
        any(term_in_text(alias.lower(), lowered) for alias in level.aliases)
        for level in EXPERIENCE_LEVELS
    )


def _mentions(text: str, words: list[str]) -> bool:
    """Vrai si un des `words` apparaît (mot entier) dans `text`."""
    t = (text or "").lower()
    return any(term_in_text(w.lower(), t) for w in words)


def _detect_active_criteria(req_data: dict, business_context: dict, req_speciality: str) -> dict:
    """
    Détermine quels critères doivent ENTRER dans la note, selon ce que
    l'exigence mentionne (logique ATS). Double source : champs parsés + dictionnaire.
    La similarité sémantique est toujours active (filet de cohérence global).
    """
    req_text = " ".join([
        str(req_data.get("job_title", "")),
        str(req_data.get("required_speciality", "")),
        " ".join(req_data.get("required_skills", []) or []),
        " ".join(req_data.get("preferred_skills", []) or []),
        " ".join(req_data.get("soft_skills", []) or []),
        " ".join(req_data.get("responsibilities", []) or []),
        " ".join(req_data.get("keywords", []) or []),
        str(req_data.get("audience_type", "")),
    ]).lower()

    has_skills = bool(req_data.get("required_skills") or req_data.get("preferred_skills"))
    fam_key = business_context.get("family_key", "")
    family_is_tech = domain_of(fam_key) == "tech" or any(
        domain_of(f) == "tech" for f in business_context.get("secondary_families", []))

    return {
        # Spécialité : presque toujours (déduite du titre, obligatoire).
        "speciality_match": bool(fam_key or req_speciality or req_data.get("job_title")),
        # Compétences : si listées, OU si poste technique (compétences implicites).
        "technical_skills": has_skills or family_is_tech or bool(req_speciality and req_speciality.strip()),
        # Expérience : si années requises OU niveau explicite détecté (junior, senior, lead...)
        # même si le mot "experience" n'apparaît pas.
        "relevant_experience": float(req_data.get("experience_required_years", 0) or 0) > 0
                               or _has_level_signal(req_text),
        # Pédagogie : si attente d'enseignement/encadrement détectée.
        "pedagogy_tutoring": bool(req_data.get("teaching_required") or req_data.get("mentoring_preferred")
                                  or req_data.get("audience_type")) or _mentions(req_text, _PEDAGOGY_DETECT),
        # Soft skills : toujours actifs. Même si l'offre ne les mentionne pas,
        # ils restent valorisés et la note monte avec les soft skills détectés dans le CV.
        "soft_skills": True,
        # Sémantique : toujours active.
        "semantic_similarity": True,
    }


def _domain_fit_multiplier(domain_fit: float) -> float:
    """
    Pénalise fortement les CV dont le DOMAINE ne correspond pas au poste.
    domain_fit (0..1) élevé => pas de pénalité ; faible => score écrasé.
      >= 0.50 : 1.00 (aucune pénalité)
      <= 0.18 : 0.25 (forte pénalité — domaine totalement différent)
      entre   : interpolation linéaire
    """
    if domain_fit >= 0.50:
        return 1.0
    if domain_fit <= 0.18:
        return 0.25
    return 0.25 + (domain_fit - 0.18) * (1.0 - 0.25) / (0.50 - 0.18)


def classify_score(score: float) -> str:
    """Traduit un score chiffré en CATÉGORIE de décision, selon des seuils
    définis dans la config (excellent > strong > moderate > sinon weak)."""
    if score >= SHORTLIST_THRESHOLDS["excellent"]:
        return "excellent"
    if score >= SHORTLIST_THRESHOLDS["strong"]:
        return "strong"
    if score >= SHORTLIST_THRESHOLDS["moderate"]:
        return "moderate"
    return "weak"


def recommendation_from_score(score: float) -> str:
    """Traduit le score en RECOMMANDATION d'action pour le recruteur :
    recommandé (entretien) / à examiner / non recommandé."""
    if score >= SHORTLIST_THRESHOLDS["strong"]:
        return "recommended"
    if score >= SHORTLIST_THRESHOLDS["moderate"]:
        return "review"
    return "not_recommended"


def compute_scoring(cv_data: dict, req_data: dict) -> dict:
    # ===== Business Context Resolver : adapter le scoring au POSTE visé =====
    # Détecte la famille de poste depuis l'exigence (texte libre) et charge
    # les pondérations métier adaptées (coach, financier, RH, accueil, ...).
    business_context = resolve_business_context(req_data)
    weights = business_context["weights"]
    family_keywords = business_context["keywords"]

    cv_speciality, cv_speciality_scores = detect_speciality_from_cv(cv_data)
    req_speciality, req_speciality_scores = detect_speciality_from_requirement(req_data)

    # ===== Adéquation de SPÉCIALITÉ (sous-spécialité précise) =====
    # Priorité à la comparaison de la spécialité PRÉCISE (Web Dev, AI/Data,
    # Mobile, Cybersécurité…). Deux profils du même grand domaine "tech" mais
    # de sous-spécialités différentes (ex: AI/Data vs Web Dev) NE doivent PAS
    # obtenir une note pleine — sinon on ne distingue pas les profils.
    if cv_speciality and req_speciality:
        if cv_speciality == req_speciality:
            speciality_ratio = 1.0                      # même sous-spécialité exacte
        else:
            speciality_ratio = 0.4                      # même domaine, sous-spé différente
    elif family_keywords:
        # Sous-spécialité indéterminée d'un côté : on retombe sur la présence des
        # mots-clés du domaine, mais PLAFONNÉE (on ne peut pas confirmer la sous-spé).
        cv_text = build_cv_semantic_text(cv_data)
        speciality_ratio = min(0.7, family_keyword_ratio(cv_text, family_keywords))
        speciality_ratio = max(speciality_ratio, 0.2)
    else:
        # Aucune spécialité détectable des deux côtés.
        speciality_ratio = 0.2

    # Compétences : couverture des exigées + bonus des compétences EN PLUS
    # pertinentes. Si l'offre ne liste rien, les MOTS-CLÉS MÉTIER (ontologie)
    # servent de compétences implicites (domain_keywords).
    skill_result = compute_skill_match(
        candidate_skills=cv_data.get("skills_technical", []),
        required_skills=req_data.get("required_skills", []),
        preferred_skills=req_data.get("preferred_skills", []),
        domain_keywords=family_keywords,
    )

    experience_result = compute_experience_match(cv_data=cv_data, req_data=req_data)
    education_result = compute_education_score(cv_data=cv_data, req_data=req_data)
    pedagogy_result = compute_pedagogy_match(cv_data=cv_data, req_data=req_data)
    soft_result = compute_soft_skill_match(
        candidate_soft_skills=cv_data.get("skills_soft", []),
        required_soft_skills=req_data.get("soft_skills", []),
    )

    # ===== Texte sémantique du poste ENRICHI =====
    # On ne base PAS la similarité sur la longueur de l'offre : une exigence de
    # 3 mots ("recruteur it multilangue") est complétée par la SIGNATURE de la
    # famille métier détectée (label + mots-clés) pour que le cosinus mesure le
    # SENS du poste, pas son volume de texte.
    req_semantic_text = build_requirement_semantic_text(req_data)
    if business_context["family_key"] or family_keywords:
        signature = (business_context["family_label"] + " "
                     + " ".join(family_keywords))
        req_semantic_text = (req_semantic_text + " " + signature).strip()

    semantic_score_ratio = compute_semantic_similarity(
        build_cv_semantic_text(cv_data),
        req_semantic_text,
    )

    # Ratios (0..1) de chaque critère.
    ratios = {
        "speciality_match": speciality_ratio,
        "technical_skills": skill_result["ratio"],
        "relevant_experience": experience_result["ratio"],
        "pedagogy_tutoring": pedagogy_result["ratio"],
        "soft_skills": soft_result["ratio"],
        "semantic_similarity": semantic_score_ratio,
    }

    # ===== Activation dynamique (type ATS) + redistribution des poids =====
    # Un critère NON mentionné dans l'exigence est exclu de la note ; son poids
    # est redistribué sur les critères actifs (renormalisation à 100).
    active = _detect_active_criteria(req_data, business_context, req_speciality)
    base_active_sum = sum(weights[c] for c in ratios if active[c]) or 1
    applied_weights = {
        c: (round(weights[c] / base_active_sum * 100, 2) if active[c] else 0.0)
        for c in ratios
    }
    # Note pondérée par critère (les critères inactifs valent 0 -> ignorés).
    weighted_scores = {c: ratios[c] * applied_weights[c] for c in ratios}

    # ===== Gate de compatibilité de DOMAINE =====
    # Empêche qu'un CV d'un autre métier obtienne un score moyen.
    # Ex : CV développeur full-stack vs poste "mécanicien voiture" => score très bas.
    cv_text_full = build_cv_semantic_text(cv_data)
    cv_family, _ = detect_family_from_text(cv_text_full)
    req_family = business_context["family_key"]
    cv_domain = domain_of(cv_family)
    req_domain = domain_of(req_family)

    # Le poste peut être HYBRIDE (ex: "recruteur IT" = people + tech) : on
    # considère TOUS les domaines présents dans l'exigence. Idem côté CV
    # (un ingénieur ayant développé une plateforme RH couvre tech + people).
    req_domains = {req_domain} | {
        domain_of(f) for f in business_context.get("secondary_families", [])
    }
    req_domains.discard("")
    cv_domains = detect_domains_from_text(cv_text_full)
    if cv_domain:
        cv_domains.add(cv_domain)

    # ===== Détection HORS-PÉRIMÈTRE (bidirectionnelle) =====
    # Un métier clairement hors du périmètre DecliTech (agriculture, mécanique,
    # droit, médical, BTP...) est traité comme un domaine "ext:<x>". Si l'exigence
    # et le CV ne partagent AUCUN domaine, le profil est "hors domaine".
    req_domain_text = " ".join([
        req_data.get("job_title", ""),
        req_data.get("required_speciality", ""),
        " ".join(req_data.get("required_skills", [])),
        " ".join(req_data.get("preferred_skills", [])),
        " ".join(req_data.get("keywords", [])),
        " ".join(req_data.get("responsibilities", [])),
        req_data.get("target_sector", ""),
    ])
    req_external = detect_external_domain(req_domain_text)
    cv_external = detect_external_domain(cv_text_full)
    # IMPORTANT : un domaine EXTERNE ne compte que si CE CÔTÉ n'a AUCUN domaine
    # DecliTech reconnu. Ainsi un simple mot incident (ex : "juridique" cité une
    # fois dans un CV clairement tech) NE fait PAS basculer le profil hors domaine.
    # Un vrai CV hors-périmètre (ex : avocat) n'a, lui, aucun domaine DecliTech.
    if req_external and not req_domains:
        req_domains.add("ext:" + req_external)
    if cv_external and not cv_domains:
        cv_domains.add("ext:" + cv_external)

    # Signal de fond : si l'offre précise des compétences, on COMBINE le sens
    # (sémantique) et le recouvrement réel de compétences. Un CV d'un autre
    # métier (0 compétence en commun) chute fortement même si la sémantique
    # trouve une vague proximité.
    has_required = bool(req_data.get("required_skills") or req_data.get("preferred_skills"))
    if has_required:
        domain_fit = 0.5 * semantic_score_ratio + 0.5 * skill_result["ratio"]
    else:
        domain_fit = semantic_score_ratio
    # Comparaison par DOMAINE LARGE (tech / people / business / health) :
    #   - même domaine    -> on garantit l'absence de pénalité
    #   - domaines différents -> on plafonne bas (CV d'un autre métier)
    out_of_scope = False
    if req_domains and cv_domains:
        if req_domains & cv_domains:
            # Au moins un domaine en commun (poste hybride inclus) => pas de pénalité
            domain_fit = max(domain_fit, 0.60)
        else:
            # Aucun domaine partagé => profil hors domaine (dans les deux sens)
            domain_fit = min(domain_fit, 0.10)
            out_of_scope = True

    # (Le knockout externe redondant a été retiré : la comparaison ensembliste
    # ci-dessus suffit et évite les faux positifs dus à un mot incident.)

    domain_multiplier = _domain_fit_multiplier(domain_fit)

    final_score = round(sum(weighted_scores.values()) * domain_multiplier, 2)
    if out_of_scope:
        # Plafond dur : un profil hors domaine ne doit jamais paraître acceptable.
        final_score = min(final_score, 20.0)
    decision_key = classify_score(final_score)
    recommendation_key = recommendation_from_score(final_score)

    return {
        "final_score": final_score,
        "decision_key": decision_key,
        "decision_label": DECISION_LABELS[decision_key],
        "recommendation_key": recommendation_key,
        "recommendation_label": RECOMMENDATION_LABELS[recommendation_key],
        "cv_speciality": cv_speciality,
        "requirement_speciality": req_speciality,
        "speciality_scores_cv": cv_speciality_scores,
        "speciality_scores_requirement": req_speciality_scores,
        "business_context": {
            "family_key": business_context["family_key"],
            "family_label": business_context["family_label"],
            "confidence": business_context["confidence"],
            "method": business_context["method"],
            "applied_weights": applied_weights,
        },
        "applied_weights": applied_weights,
        "active_criteria": active,
        "base_weights": weights,
        "domain_fit": round(domain_fit, 3),
        "domain_multiplier": round(domain_multiplier, 3),
        "cv_family": cv_family,
        "cv_domain": cv_domain,
        "requirement_domain": req_domain,
        "cv_domains": sorted(cv_domains),
        "requirement_domains": sorted(req_domains),
        "out_of_scope": out_of_scope,
        "cv_external_domain": cv_external,
        "requirement_external_domain": req_external,
        "weighted_scores": {k: round(v, 2) for k, v in weighted_scores.items()},
        "skill_result": skill_result,
        "experience_result": experience_result,
        "education_result": education_result,
        "pedagogy_result": pedagogy_result,
        "soft_result": soft_result,
        "semantic_similarity_ratio": round(semantic_score_ratio, 4),
    }
