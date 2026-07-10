from __future__ import annotations

from src.utils import normalize_list

_SKILL_MAP = {
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "c sharp": "C#",
    "csharp": "C#",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "springboot": "Spring Boot",
    "ml": "Machine Learning",
    "ai": "AI",
    "nlp": "NLP",
    "html5": "HTML",
    "css3": "CSS",
}

_LANGUAGE_MAP = {
    "anglais": "English",
    "français": "French",
    "french": "French",
    "english": "English",
    "arabic": "Arabic",
    "arabe": "Arabic",
}

_SOFT_MAP = {
    "travail en équipe": "Teamwork",
    "team work": "Teamwork",
    "teamwork": "Teamwork",
    "communication skills": "Communication",
    "communication": "Communication",
    "empathie": "Empathy",
    "empathy": "Empathy",
    "patience": "Patience",
    "pedagogy": "Pedagogy",
    "pédagogie": "Pedagogy",
}


def _normalize_skill(value: str) -> str:
    lowered = value.strip().lower()
    return _SKILL_MAP.get(lowered, value.strip())


def _normalize_language(value: str) -> str:
    lowered = value.strip().lower()
    return _LANGUAGE_MAP.get(lowered, value.strip())


def _normalize_soft_skill(value: str) -> str:
    lowered = value.strip().lower()
    return _SOFT_MAP.get(lowered, value.strip())


def _normalize_projects(projects: list) -> list[str]:
    """Convert project items to strings, handling both string and dict formats."""
    result = []
    for proj in projects:
        if isinstance(proj, str):
            result.append(proj.strip())
        elif isinstance(proj, dict):
            name = proj.get("name", "Project")
            skills = proj.get("skills", [])
            if isinstance(skills, list):
                skills_str = ", ".join(str(s).strip() for s in skills if s)
                if skills_str:
                    result.append(f"{name} ({skills_str})")
                else:
                    result.append(name)
            else:
                result.append(name)
        else:
            result.append(str(proj).strip())
    return [p for p in result if p]


def normalize_cv_data(cv_data: dict) -> dict:
    cv_data["skills_technical"] = normalize_list([_normalize_skill(v) for v in cv_data.get("skills_technical", [])])
    cv_data["skills_soft"] = normalize_list([_normalize_soft_skill(v) for v in cv_data.get("skills_soft", [])])
    cv_data["languages"] = normalize_list([_normalize_language(v) for v in cv_data.get("languages", [])])
    cv_data["certifications"] = normalize_list(cv_data.get("certifications", []))
    cv_data["projects"] = normalize_list(_normalize_projects(cv_data.get("projects", [])))
    cv_data["teaching_signals"] = normalize_list(cv_data.get("teaching_signals", []))
    cv_data["mentoring_signals"] = normalize_list(cv_data.get("mentoring_signals", []))
    cv_data["youth_education_signals"] = normalize_list(cv_data.get("youth_education_signals", []))

    for exp in cv_data.get("experience", []):
        exp["skills_used"] = normalize_list([_normalize_skill(v) for v in exp.get("skills_used", [])])

    return cv_data


def normalize_requirement_data(req_data: dict) -> dict:
    req_data["required_skills"] = normalize_list([_normalize_skill(v) for v in req_data.get("required_skills", [])])
    req_data["preferred_skills"] = normalize_list([_normalize_skill(v) for v in req_data.get("preferred_skills", [])])
    req_data["soft_skills"] = normalize_list([_normalize_soft_skill(v) for v in req_data.get("soft_skills", [])])
    req_data["languages_required"] = normalize_list([_normalize_language(v) for v in req_data.get("languages_required", [])])
    req_data["education_requirements"] = normalize_list(req_data.get("education_requirements", []))
    req_data["responsibilities"] = normalize_list(req_data.get("responsibilities", []))
    req_data["keywords"] = normalize_list(req_data.get("keywords", []))
    req_data["priority_criteria"] = normalize_list(req_data.get("priority_criteria", []))
    return req_data
