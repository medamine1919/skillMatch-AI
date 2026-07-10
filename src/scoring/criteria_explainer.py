"""
Criteria Explainer (XAI) — explique EN FRANÇAIS pourquoi chaque critère a obtenu
son score, à partir des détails réels du calcul. Sert l'explicabilité du modèle
(pourquoi un critère vaut 0, ce qui manque, ce qui a matché).
"""
from __future__ import annotations


def _fmt(items, n=4):
    items = [str(i) for i in (items or []) if str(i).strip()]
    return ", ".join(items[:n])


def build_criteria_explanations(result: dict) -> dict:
    """
    Retourne un dict { criterion_key: { "status", "text" } } pour les 6 critères.
    status ∈ {"good","partial","bad"} (pour la couleur côté UI).
    """
    ws = result.get("weighted_scores", {})
    weights = result.get("applied_weights", {})
    skill = result.get("skill_result", {})
    exp = result.get("experience_result", {})
    ped = result.get("pedagogy_result", {})
    soft = result.get("soft_result", {})
    biz = result.get("business_context", {})
    family = biz.get("family_label", "")

    out = {}

    def status_of(key):
        """Détermine l'état d'un critère en comparant la note obtenue à son poids.
        Sert à colorer l'UI : vert (good) / orange (partial) / rouge (bad).
        'neutral' si le critère ne compte pas pour ce poste (poids 0)."""
        w = weights.get(key, 0) or 0       # poids appliqué (max possible)
        got = ws.get(key, 0) or 0          # note réellement obtenue
        if w == 0:
            return "neutral"               # critère non pertinent pour ce poste
        pct = got / w                      # taux de réussite du critère (0..1)
        if pct >= 0.7:
            return "good"
        if pct > 0:
            return "partial"
        return "bad"

    # ---- Spécialité ----
    cv_spec = result.get("cv_speciality", "")
    cv_dom = result.get("cv_domain", "")
    req_dom = result.get("requirement_domain", "")
    s = status_of("speciality_match")
    if s == "good":
        txt = f"Le profil du candidat correspond bien au domaine attendu" + (f" ({family})." if family else ".")
    elif s == "partial":
        txt = f"Le profil est partiellement aligné avec le poste" + (f" ({family})." if family else ".")
    else:
        txt = "Le domaine du CV ne correspond pas à celui attendu pour ce poste."
        if cv_dom and req_dom and cv_dom != req_dom:
            txt += f" Domaine du CV : « {cv_dom} », domaine du poste : « {req_dom} »."
    out["speciality_match"] = {"status": s, "text": txt}

    # ---- Compétences techniques ----
    matched = skill.get("matched_required", []) + skill.get("matched_preferred", [])
    missing = skill.get("missing_required", [])
    s = status_of("technical_skills")
    if not matched and not missing:
        txt = "Aucune compétence n'était précisée dans l'offre : ce critère n'a pas pu être évalué."
    elif s == "bad":
        txt = "Aucune des compétences requises n'a été trouvée dans le CV."
        if missing:
            txt += f" Manquantes : {_fmt(missing)}."
    elif s == "partial":
        txt = f"Compétences trouvées : {_fmt(matched)}." if matched else "Peu de compétences correspondent."
        if missing:
            txt += f" Manquantes : {_fmt(missing)}."
    else:
        txt = f"La plupart des compétences requises sont présentes : {_fmt(matched)}."
    out["technical_skills"] = {"status": s, "text": txt}

    # ---- Expérience ----
    cy = exp.get("candidate_years", 0)
    ry = exp.get("required_years", 0)
    req_level_label = exp.get("required_level_label", "")
    cand_level_label = exp.get("candidate_level_label", "")
    level_alignment = exp.get("level_alignment", None)
    req_level_explicit = bool(exp.get("required_level_explicit", False))
    cand_level_explicit = bool(exp.get("candidate_level_explicit", False))
    s = status_of("relevant_experience")
    if ry and ry > 0:
        txt = f"Le candidat a ~{cy:g} an(s) d'expérience pour {ry:g} requis."
        if req_level_explicit or cand_level_explicit:
            txt += (
                f" Niveau demandé : {req_level_label or 'non précisé'} ; "
                f"niveau détecté dans le CV : {cand_level_label or 'non précisé'}."
            )
        if level_alignment is not None:
            txt += f" Compatibilité de niveau : {round(float(level_alignment) * 100):.0f}%."
        if s == "bad" or (cy or 0) < (ry or 0):
            txt += " L'expérience est insuffisante par rapport au poste."
    else:
        txt = ("Expérience/projets détectés dans le CV." if (cy or 0) > 0
               else "Peu ou pas d'expérience professionnelle détectée dans le CV.")
        if req_level_explicit or cand_level_explicit:
            txt += (
                f" Niveau demandé : {req_level_label or 'non précisé'} ; "
                f"niveau détecté dans le CV : {cand_level_label or 'non précisé'}."
            )
    out["relevant_experience"] = {"status": s, "text": txt}

    # ---- Pédagogie / tutorat ----
    signals = ped.get("signals_found", [])
    s = status_of("pedagogy_tutoring")
    if (weights.get("pedagogy_tutoring", 0) or 0) == 0:
        txt = "Ce poste n'exige pas de compétences pédagogiques : critère non pris en compte."
    elif signals:
        txt = f"Signaux pédagogiques détectés : {_fmt(signals)}."
    else:
        txt = ("Aucun signal pédagogique détecté dans le CV (aucune mention d'enseignement, "
               "formation, tutorat, coaching ou animation). C'est pourquoi ce critère est à 0.")
    out["pedagogy_tutoring"] = {"status": s, "text": txt}

    # ---- Soft skills ----
    matched_soft = soft.get("matched", [])
    missing_soft = soft.get("missing", [])
    s = status_of("soft_skills")
    if matched_soft:
        txt = f"Soft skills détectées : {_fmt(matched_soft)}."
        if missing_soft:
            txt += f" Attendues mais absentes : {_fmt(missing_soft)}."
    elif missing_soft:
        txt = f"Les soft skills attendues n'ont pas été trouvées : {_fmt(missing_soft)}."
    else:
        txt = "Peu de compétences comportementales détectées dans le CV."
    out["soft_skills"] = {"status": s, "text": txt}

    # ---- Compétences : on enrichit le texte avec le BONUS (compétences en plus) ----
    extra = skill.get("extra_relevant", [])
    if extra and out.get("technical_skills", {}).get("status") in ("good", "partial"):
        out["technical_skills"]["text"] += f" Bonus : compétences supplémentaires pertinentes ({_fmt(extra)})."

    # ---- Similarité sémantique ----
    sim = result.get("semantic_similarity_ratio", 0) or 0
    s = status_of("semantic_similarity")
    pct = round(sim * 100)
    if s == "good":
        txt = f"Forte proximité de sens entre le CV et la fiche de poste ({pct}%)."
    elif s == "partial":
        txt = f"Proximité de sens modérée entre le CV et le poste ({pct}%)."
    else:
        txt = f"Faible proximité de sens entre le CV et le poste ({pct}%)."
    out["semantic_similarity"] = {"status": s, "text": txt}

    # ---- Critères NON DEMANDÉS dans l'exigence -> marqués "inactif" ----
    # (logique ATS : on n'évalue que ce que le recruteur a demandé)
    active = result.get("active_criteria", {})
    for key in out:
        if active and active.get(key) is False:
            out[key] = {
                "status": "inactive",
                "text": "Critère non demandé dans l'exigence du poste — non pris en compte dans la note.",
            }

    return out
