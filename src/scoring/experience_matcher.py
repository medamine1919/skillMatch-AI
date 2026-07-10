"""
Évaluation de l'EXPÉRIENCE professionnelle d'un candidat par rapport au poste.

PRINCIPE : on compare le nombre d'années d'expérience du candidat au nombre
d'années EXIGÉ par l'offre, et on en déduit un ratio entre 0 et 1.
Ce ratio sera ensuite multiplié par le poids du critère "expérience" dans le
moteur de scoring global (scoring_engine.py).

Cas particulier IMPORTANT : si l'offre ne précise PAS d'années requises (cas
très fréquent quand le recruteur écrit une exigence courte), on ne peut pas
calculer un ratio classique. On applique alors une logique "neutre-positive".
"""
from __future__ import annotations

import unicodedata

from src.scoring.experience_levels import (
    EXPERIENCE_LEVELS,
    compare_levels,
    compare_level_to_years,
    detect_level_from_text,
    detect_level_from_years,
    extract_years_hint,
)
from src.scoring.synonyms import term_in_text, text_contains_term


def _build_requirement_text(req_data: dict) -> str:
    return " ".join([
        str(req_data.get("raw_text", "")),
        str(req_data.get("job_title", "")),
        str(req_data.get("required_speciality", "")),
        " ".join(req_data.get("required_skills", []) or []),
        " ".join(req_data.get("preferred_skills", []) or []),
        " ".join(req_data.get("responsibilities", []) or []),
        " ".join(req_data.get("keywords", []) or []),
        " ".join(req_data.get("priority_criteria", []) or []),
    ])


def _build_candidate_text(cv_data: dict) -> str:
    experience_bits: list[str] = []
    for exp in cv_data.get("experience", []) or []:
        if not isinstance(exp, dict):
            continue
        experience_bits.append(str(exp.get("job_title", exp.get("title", ""))))
        experience_bits.append(str(exp.get("description", "")))
    return " ".join([
        str(cv_data.get("raw_text", "")),
        str(cv_data.get("summary", "")),
        " ".join(cv_data.get("skills_technical", []) or []),
        " ".join(cv_data.get("skills_soft", []) or []),
        " ".join(cv_data.get("projects", []) or []),
        " ".join(cv_data.get("certifications", []) or []),
        " ".join(experience_bits),
    ])


def _has_explicit_level_signal(text: str) -> bool:
    lowered = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii").lower()
    if extract_years_hint(lowered) is not None:
        return True
    return any(
        any(text_contains_term(lowered, unicodedata.normalize("NFKD", alias).encode("ascii", "ignore").decode("ascii").lower()) for alias in level.aliases)
        for level in EXPERIENCE_LEVELS
    )


def compute_experience_match(cv_data: dict, req_data: dict) -> dict:
    """
    Évalue l'adéquation d'EXPÉRIENCE, en comprenant à la fois :
      - les NIVEAUX en toutes lettres (junior, confirmé, senior, lead, manager…)
      - les ANNÉES (ex: "3 ans d'expérience").

    Principe : on détecte le niveau EXIGÉ et le niveau du CANDIDAT, puis on
    compare. Un junior face à un poste senior est pénalisé ; un candidat de
    niveau égal ou supérieur obtient 1.0.
    """
    required_years = float(req_data.get("experience_required_years", 0) or 0)
    candidate_years = float(cv_data.get("estimated_years_experience", 0) or 0)

    req_text = _build_requirement_text(req_data)
    cv_text = _build_candidate_text(cv_data)
    req_has_explicit_level = _has_explicit_level_signal(req_text)
    cv_has_explicit_level = _has_explicit_level_signal(cv_text)

    # Années éventuellement trouvées dans les textes (ex: "5 ans").
    req_years_eff = required_years or (extract_years_hint(req_text) or 0.0)
    cv_years_eff = candidate_years or (extract_years_hint(cv_text) or 0.0)

    # ----- Niveau EXIGÉ : priorité au texte explicite, sinon aux années -----
    if req_has_explicit_level:
        required_level = detect_level_from_text(req_text)
    elif req_years_eff > 0:
        required_level = detect_level_from_years(req_years_eff)
    else:
        required_level = None   # aucune exigence d'expérience exploitable

    # ----- Niveau du CANDIDAT : idem -----
    if cv_has_explicit_level:
        candidate_level = detect_level_from_text(cv_text)
    elif cv_years_eff > 0:
        candidate_level = detect_level_from_years(cv_years_eff)
    else:
        candidate_level = detect_level_from_years(0)   # junior par défaut

    base = {
        "required_years": required_years,
        "candidate_years": candidate_years,
        "candidate_level": candidate_level.key,
        "candidate_level_label": candidate_level.label,
        "required_level_explicit": req_has_explicit_level,
        "candidate_level_explicit": cv_has_explicit_level,
        "required_years_hint": req_years_eff,
        "candidate_years_hint": cv_years_eff,
    }

    # ----- Cas A : aucune exigence d'expérience exploitable (ni niveau ni années) -----
    # Neutre-positif : on valorise simplement la présence d'une expérience.
    if required_level is None:
        ratio = 1.0 if (cv_years_eff > 0 or cv_data.get("experience") or cv_data.get("projects")) else 0.5
        base.update({"ratio": ratio, "required_level": "", "required_level_label": "Non précisé",
                     "level_alignment": 1.0})
        return base

    # Alignement de niveau (1.0 si candidat >= exigé ; pénalité sinon).
    level_alignment = compare_levels(required_level, candidate_level)

    # ----- Cas B : niveau exigé connu -----
    if req_years_eff > 0 and cv_years_eff > 0:
        # Niveau ET années des deux côtés : on mélange alignement + ratio d'années.
        years_ratio = min(cv_years_eff / req_years_eff, 1.0)
        ratio = round(0.5 * level_alignment + 0.5 * years_ratio, 3)
    else:
        # Seul le niveau est exploitable : le score = l'alignement de niveau
        # (junior vs senior -> 0.45, mid vs senior -> 0.75, senior+ -> 1.0).
        ratio = round(level_alignment, 3)

    base.update({
        "ratio": max(0.0, min(1.0, ratio)),
        "required_level": required_level.key,
        "required_level_label": required_level.label,
        "level_alignment": level_alignment,
    })
    return base
