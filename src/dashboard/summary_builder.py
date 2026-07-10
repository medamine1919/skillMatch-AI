from __future__ import annotations


def build_summary_cards(result: dict) -> dict:
    return {
        "final_score": result.get("final_score", 0),
        "decision_label": result.get("decision_label", ""),
        "recommendation_label": result.get("recommendation_label", ""),
        "cv_speciality": result.get("cv_speciality", ""),
        "requirement_speciality": result.get("requirement_speciality", ""),
        "semantic_similarity_ratio": result.get("semantic_similarity_ratio", 0),
    }


def build_declitech_fit_summary(cv_data: dict, req_data: dict, result: dict) -> dict:
    candidate_skills = " ".join(
        [
            " ".join(cv_data.get("skills_technical", [])),
            " ".join(cv_data.get("skills_soft", [])),
            " ".join(cv_data.get("projects", [])),
            " ".join(cv_data.get("teaching_signals", [])),
            " ".join(cv_data.get("mentoring_signals", [])),
            " ".join(cv_data.get("youth_education_signals", [])),
            " ".join(req_data.get("keywords", [])),
        ]
    ).lower()

    pillars = []

    if any(term in candidate_skills for term in ["python", "ai", "machine learning", "data", "dashboard", "power bi", "sql", "nlp"]):
        pillars.append("AI, data et dashboards analytiques")
    if any(term in candidate_skills for term in ["html", "css", "javascript", "typescript", "spring boot", "angular", "react", "node.js", "web"]):
        pillars.append("développement logiciel et web")
    if any(term in candidate_skills for term in ["arduino", "robotics", "embedded", "c++", "electronics", "sensors", "microcontroller"]):
        pillars.append("robotique, Arduino et systèmes embarqués")
    if any(term in candidate_skills for term in ["teaching", "tutoring", "pedagogy", "children", "kids", "teen", "training", "formation", "workshop"]):
        pillars.append("formation, pédagogie et accompagnement des jeunes")
    if any(term in candidate_skills for term in ["automation", "process", "workflow", "digit", "platform", "matching", "cv"]):
        pillars.append("solutions digitales et automatisation de processus")

    if not pillars:
        pillars.append("innovation numérique et expertise technique polyvalente")

    return {
        "summary": f"Score final {result.get('final_score', 0)}/100 avec une spécialité détectée en {result.get('cv_speciality', '') or 'non précisée'}.",
        "fit_pillars": pillars[:4],
        "declitech_focus": (
            "Le profil semble le plus proche des activités de Declitech sur "
            + ", ".join(pillars[:3])
            + "."
        ),
        "hire_view": result.get("recommendation_label", ""),
    }
