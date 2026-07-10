"""
Matching des COMPÉTENCES techniques — logique ATS "couverture + bonus".

Principe (validé avec le métier) :
    Note = 0.85 × couverture des compétences EXIGÉES   (manquant -> pénalité)
         + 0.15 × bonus compétences EN PLUS pertinentes (récompense la richesse)

- La couverture mesure combien des compétences demandées sont présentes dans le CV.
  Chaque compétence requise absente fait baisser la note (pénalité naturelle).
- Le bonus récompense les compétences SUPPLÉMENTAIRES du CV qui sont pertinentes
  au DOMAINE (validées par le dictionnaire de synonymes / l'ontologie). Plafonné,
  il permet de distinguer deux profils sans jamais compenser un manque.

Le matching exigé ↔ CV s'appuie sur :
  - le DICTIONNAIRE de synonymes (terms_equivalent : FR/EN, abréviations…)
  - un repli flou (rapidfuzz) pour les fautes de frappe / variantes.
"""
from __future__ import annotations

from rapidfuzz import fuzz

from src.scoring.synonyms import terms_equivalent

COVERAGE_WEIGHT = 0.85   # part de la note venant de la couverture des exigences
BONUS_WEIGHT = 0.15      # part venant des compétences supplémentaires pertinentes
BONUS_FULL = 3.0         # nb de compétences "en plus" pour atteindre le bonus maximal


def _fuzzy(a: str, b: str) -> float:
    a, b = a.lower(), b.lower()
    return max(fuzz.ratio(a, b), fuzz.token_set_ratio(a, b)) / 100.0


def _matches(term: str, candidates: list[str]) -> bool:
    """Vrai si `term` (compétence exigée) est présent dans le CV, via
    le dictionnaire (équivalents/synonymes) OU une similarité floue >= 0.75."""
    return any(terms_equivalent(term, c) or _fuzzy(term, c) >= 0.75 for c in candidates)


def compute_skill_match(
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
    domain_keywords: list[str] | None = None,
) -> dict:
    cand = candidate_skills or []
    required = required_skills or []
    preferred = preferred_skills or []
    domain = domain_keywords or []

    # ---------- 1) COUVERTURE des compétences demandées ----------
    matched_required = [s for s in required if _matches(s, cand)]
    missing_required = [s for s in required if s not in matched_required]
    matched_preferred = [s for s in preferred if _matches(s, cand)]

    if required or preferred:
        req_cov = (len(matched_required) / len(required)) if required else 0.0
        pref_cov = (len(matched_preferred) / len(preferred)) if preferred else 0.0
        # Les compétences OBLIGATOIRES pèsent plus que les souhaitées.
        if required and preferred:
            coverage = 0.8 * req_cov + 0.2 * pref_cov
        elif required:
            coverage = req_cov
        else:
            coverage = pref_cov
    elif domain:
        # Aucune compétence explicite : on utilise les mots-clés du DOMAINE
        # (ontologie) comme compétences implicites attendues.
        matched_domain = [k for k in domain if _matches(k, cand)]
        coverage = min(1.0, len(matched_domain) / 4.0)
    else:
        # Rien d'exigé et pas de domaine -> critère non évaluable.
        return {"ratio": 0.0, "matched_required": [], "missing_required": [],
                "matched_preferred": [], "extra_relevant": []}

    # ---------- 2) BONUS : compétences EN PLUS pertinentes au domaine ----------
    covered_terms = required + preferred + domain
    extras = [c for c in cand
              if not any(terms_equivalent(c, t) or _fuzzy(c, t) >= 0.75 for t in covered_terms)]
    # Une compétence "en plus" ne compte QUE si elle est pertinente au domaine
    # (reconnue par le dictionnaire comme équivalente à un mot-clé du domaine).
    relevant_extra = [c for c in extras if any(terms_equivalent(c, k) for k in domain)]
    bonus_fraction = min(1.0, len(relevant_extra) / BONUS_FULL) if domain else 0.0

    # ---------- 3) Note finale (plafonnée à 1.0) ----------
    ratio = COVERAGE_WEIGHT * coverage + BONUS_WEIGHT * bonus_fraction
    ratio = max(0.0, min(1.0, ratio))

    return {
        "ratio": ratio,
        "matched_required": matched_required,
        "missing_required": missing_required,
        "matched_preferred": matched_preferred,
        "extra_relevant": relevant_extra,       # compétences en plus (bonus)
    }
