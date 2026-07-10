"""
EXPLANATION ENGINE — génère des explications TEXTUELLES du résultat de scoring.

Deux niveaux :
  - build_short_explanation  : un paragraphe de synthèse (vue rapide).
  - build_detailed_explanation : un rapport ligne par ligne (sous-scores,
    compétences trouvées/manquantes, expérience, signaux pédagogiques...).

Ces textes servent l'EXPLICABILITÉ (XAI) : justifier le score auprès du
recruteur, plutôt que de livrer un chiffre "boîte noire".
"""
from __future__ import annotations


def build_short_explanation(result: dict) -> str:
    """Construit un court paragraphe de synthèse à partir du résultat de scoring."""
    cv_spec = result.get("cv_speciality", "Unknown")
    req_spec = result.get("requirement_speciality", "Unknown")
    score = result.get("final_score", 0)
    missing_required = result.get("skill_result", {}).get("missing_required", [])
    pedagogy_signals = result.get("pedagogy_result", {}).get("signals_found", [])

    parts = [
        f"The candidate shows a {result.get('decision_label', 'moderate')} with a final score of {score}/100 for Declitech's digital and training activities.",
        f"Detected speciality: {cv_spec}; target speciality: {req_spec}.",
    ]

    if missing_required:
        parts.append(f"Some important skills are still missing, especially: {', '.join(missing_required[:3])}.")
    else:
        parts.append("The core technical requirements are largely covered.")

    if pedagogy_signals:
        parts.append(f"Positive tutoring/pedagogical signals were found: {', '.join(pedagogy_signals[:2])}, which fits Declitech's training programs for youth and learners.")

    if any(term in (" ".join(result.get("skill_result", {}).get("matched_required", []) + result.get("skill_result", {}).get("matched_preferred", []))).lower() for term in ["ai", "data", "python", "web", "angular", "spring boot", "arduino", "robotics"]):
        parts.append("The profile aligns with Declitech's focus on smart technologies, software development, and robotics.")

    return " ".join(parts)


def build_detailed_explanation(cv_data: dict, req_data: dict, result: dict) -> str:
    """Construit un rapport détaillé multi-lignes (sous-scores + détails par critère)."""
    skill_result = result.get("skill_result", {})
    lines = [
        f"Final score: {result.get('final_score', 0)}/100",
        f"Decision: {result.get('decision_label', '')}",
        f"Recommendation: {result.get('recommendation_label', '')}",
        f"Detected candidate speciality: {result.get('cv_speciality', '')}",
        f"Detected target speciality: {result.get('requirement_speciality', '')}",
        "",
        "Subscores:",
    ]

    for key, value in result.get("weighted_scores", {}).items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "",
            "Matched required skills: " + ", ".join(skill_result.get("matched_required", [])) if skill_result.get("matched_required") else "Matched required skills: none",
            "Missing required skills: " + ", ".join(skill_result.get("missing_required", [])) if skill_result.get("missing_required") else "Missing required skills: none",
            "Matched preferred skills: " + ", ".join(skill_result.get("matched_preferred", [])) if skill_result.get("matched_preferred") else "Matched preferred skills: none",
            "",
            f"Candidate estimated years of experience: {result.get('experience_result', {}).get('candidate_years', 0)}",
            f"Required years of experience: {result.get('experience_result', {}).get('required_years', 0)}",
            "",
            "Pedagogical/tutoring signals: "
            + (", ".join(result.get("pedagogy_result", {}).get("signals_found", [])) or "none"),
            "Soft skills matched: "
            + (", ".join(result.get("soft_result", {}).get("matched", [])) or "none"),
        ]
    )

    return "\n".join(lines)
