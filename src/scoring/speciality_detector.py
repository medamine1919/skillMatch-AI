from __future__ import annotations

from src.constants import TECH_SPECIALITY_HINTS
from src.utils import safe_lower


def _count_hits(text: str, hints: list[str]) -> int:
    lowered = safe_lower(text)
    return sum(1 for hint in hints if safe_lower(hint) in lowered)


def detect_speciality_from_cv(cv_data: dict) -> tuple[str, dict[str, int]]:
    text_parts = [
        cv_data.get("summary", ""),
        " ".join(cv_data.get("skills_technical", [])),
        " ".join(cv_data.get("projects", [])),
    ]
    for exp in cv_data.get("experience", []):
        text_parts.append(exp.get("job_title", ""))
        text_parts.append(exp.get("description", ""))
        text_parts.append(" ".join(exp.get("skills_used", [])))

    combined_text = " ".join(text_parts)
    scores = {spec: _count_hits(combined_text, hints) for spec, hints in TECH_SPECIALITY_HINTS.items()}

    best_spec = max(scores, key=scores.get) if scores else ""
    # Aucun mot-clé IT détecté => spécialité INDÉTERMINÉE (et surtout PAS "Web Dev"
    # par défaut, ce qui faisait matcher à tort des CV hors-domaine).
    if scores.get(best_spec, 0) == 0:
        best_spec = ""
    return best_spec, scores


def detect_speciality_from_requirement(req_data: dict) -> tuple[str, dict[str, int]]:
    text_parts = [
        req_data.get("job_title", ""),
        req_data.get("required_speciality", ""),
        " ".join(req_data.get("required_skills", [])),
        " ".join(req_data.get("preferred_skills", [])),
        " ".join(req_data.get("keywords", [])),
        " ".join(req_data.get("responsibilities", [])),
    ]
    combined_text = " ".join(text_parts)
    scores = {spec: _count_hits(combined_text, hints) for spec, hints in TECH_SPECIALITY_HINTS.items()}

    best_spec = req_data.get("required_speciality", "").strip()
    if best_spec and best_spec in TECH_SPECIALITY_HINTS:
        return best_spec, scores

    best_spec = max(scores, key=scores.get) if scores else ""
    # Pas de mot-clé IT dans l'exigence => spécialité INDÉTERMINÉE (pas de
    # "Web Dev" forcé, qui rendait compatible n'importe quel poste hors-IT).
    if scores.get(best_spec, 0) == 0:
        best_spec = ""
    return best_spec, scores
 