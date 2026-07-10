from __future__ import annotations

import json
import re
import unicodedata

from src.config import RESOURCES_DIR
from src.constants import CHILD_FRIENDLY_SOFT_SKILLS, TECH_SPECIALITY_HINTS


_EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
_PHONE_PATTERN = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
_YEAR_PATTERN = re.compile(r"(?:19|20)\d{2}")
_YEAR_RANGE_PATTERN = re.compile(
    r"\b((?:19|20)\d{2})\s*(?:-|to|a|au|/|until|till)\s*((?:19|20)\d{2}|present|current|now|aujourdhui)\b",
    re.IGNORECASE,
)

_LANGUAGE_HINTS = {
    "english": "English",
    "anglais": "English",
    "french": "French",
    "francais": "French",
    "français": "French",
    "arabic": "Arabic",
    "arabe": "Arabic",
    "spanish": "Spanish",
    "espagnol": "Spanish",
    "german": "German",
    "allemand": "German",
    "italian": "Italian",
    "italien": "Italian",
}

_NON_TECHNICAL_HINTS = {
    "education",
    "teaching",
    "tutoring",
    "tutor",
    "trainer",
    "training",
    "workshop",
    "workshops",
    "mentor",
    "mentoring",
    "coaching",
    "pedagogy",
    "children",
    "kids",
    "teenagers",
}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(normalized.lower().split())


def _unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item.strip())
    return result


def _skill_present(normalized_text: str, skill: str) -> bool:
    normalized_skill = _normalize(skill)
    if not normalized_skill:
        return False
    if normalized_skill in {"c", "ai"}:
        return bool(re.search(rf"(?<!\w){re.escape(normalized_skill)}(?!\w)", normalized_text))
    if " " in normalized_skill or "+" in normalized_skill or "-" in normalized_skill:
        return normalized_skill in normalized_text
    return bool(re.search(rf"(?<!\w){re.escape(normalized_skill)}(?!\w)", normalized_text))


def _load_json_list(filename: str, default: list[str]) -> list[str]:
    path = RESOURCES_DIR / filename
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                values: list[str] = []
                for entry in payload.values():
                    if isinstance(entry, list):
                        values.extend(str(item) for item in entry)
                    elif isinstance(entry, str):
                        values.append(entry)
                return _unique_preserve_order(values)
            if isinstance(payload, list):
                return _unique_preserve_order([str(item) for item in payload])
    except Exception:
        pass
    return _unique_preserve_order(default)


def _extract_name(lines: list[str], email: str) -> str:
    candidates = [line for line in lines[:6] if line and "@" not in line and len(line.split()) <= 6]
    for candidate in candidates:
        clean = candidate.strip("-•*\t ")
        if len(clean) >= 3 and not any(char.isdigit() for char in clean):
            return clean
    if email:
        local_part = email.split("@", 1)[0]
        parts = [part for part in re.split(r"[._-]+", local_part) if part]
        if parts:
            return " ".join(part.capitalize() for part in parts[:4])
    return "Candidat"


def _extract_location(lines: list[str], text: str) -> str:
    patterns = [
        r"(?:location|localisation|adresse)\s*[:\-]\s*([^\n\r]+)",
        r"(?:based in|lives in|resides in)\s+([^\n\r]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().strip(".\n\r")[:120]
    for line in lines[:12]:
        if any(token in _normalize(line) for token in ["tunis", "sfax", "sousse", "monastir", "alger", "casablanca", "rabat", "paris"]):
            return line.strip()[:120]
    return ""


def _extract_skills(normalized_text: str) -> list[str]:
    skills: list[str] = []
    for speciality_skills in TECH_SPECIALITY_HINTS.values():
        for skill in speciality_skills:
            normalized_skill = _normalize(skill)
            if normalized_skill in _NON_TECHNICAL_HINTS:
                continue
            if _skill_present(normalized_text, skill):
                skills.append(skill)
    return _unique_preserve_order(skills)


def _extract_soft_skills(normalized_text: str) -> list[str]:
    signals = _load_json_list("pedagogical_signals.json", CHILD_FRIENDLY_SOFT_SKILLS)
    soft = [skill for skill in CHILD_FRIENDLY_SOFT_SKILLS if _normalize(skill) in normalized_text]
    soft.extend(signal for signal in signals if _normalize(signal) in normalized_text)
    return _unique_preserve_order(soft)


def _extract_languages(normalized_text: str) -> list[str]:
    languages = [label for key, label in _LANGUAGE_HINTS.items() if key in normalized_text]
    return _unique_preserve_order(languages)


def _extract_certifications(lines: list[str], normalized_text: str) -> list[str]:
    cert_lines = []
    for line in lines:
        lowered = _normalize(line)
        if any(keyword in lowered for keyword in ["certification", "certificate", "certified", "certificat"]):
            cert_lines.append(line.strip("-•*\t "))
    if not cert_lines and "certif" in normalized_text:
        cert_lines.append("Certification détectée")
    return _unique_preserve_order(cert_lines)


def _extract_projects(lines: list[str], normalized_text: str) -> list[str]:
    projects = []
    for line in lines:
        lowered = _normalize(line)
        if "project" in lowered or "projet" in lowered:
            projects.append(line.strip("-•*\t "))
    if not projects and "project" in normalized_text:
        projects.append("Projet mentionné dans le CV")
    return _unique_preserve_order(projects)


def _extract_teaching_signals(normalized_text: str) -> list[str]:
    signals = ["teaching", "tutoring", "tutor", "mentor", "mentoring", "coaching", "workshop", "training", "education", "pedagogy"]
    return _unique_preserve_order([signal for signal in signals if signal in normalized_text])


def _extract_youth_signals(normalized_text: str) -> list[str]:
    signals = ["children", "kids", "teen", "teenager", "adolescent", "young", "youth"]
    return _unique_preserve_order([signal for signal in signals if signal in normalized_text])


def _extract_mentoring_signals(normalized_text: str) -> list[str]:
    signals = ["mentor", "mentoring", "coaching", "guidance", "accompagnement"]
    return _unique_preserve_order([signal for signal in signals if signal in normalized_text])


def _extract_experience(lines: list[str], normalized_text: str) -> list[dict]:
    experience: list[dict] = []
    for line in lines:
        if _YEAR_RANGE_PATTERN.search(line) or any(keyword in _normalize(line) for keyword in ["experience", "work", "employment", "internship", "stage", "job"]):
            experience.append({
                "job_title": line.strip("-•*\t ")[:120],
                "company": "",
                "start_date": "",
                "end_date": "",
                "duration_months": 0,
                "description": line.strip(),
                "skills_used": [],
            })
    return experience[:8]


def _extract_education(lines: list[str], normalized_text: str) -> list[dict]:
    education: list[dict] = []
    for line in lines:
        lowered = _normalize(line)
        if any(keyword in lowered for keyword in ["education", "formation", "degree", "master", "bachelor", "licence", "engineer", "diploma", "certificate"]):
            education.append({
                "degree": line.strip("-•*\t ")[:120],
                "field": "",
                "institution": "",
                "start_date": "",
                "end_date": "",
            })
    return education[:8]


def _estimate_experience_years(normalized_text: str) -> float:
    ranges = list(_YEAR_RANGE_PATTERN.finditer(normalized_text))
    if ranges:
        total = 0.0
        for match in ranges:
            start_year = int(match.group(1))
            end_token = match.group(2)
            if end_token.isdigit():
                total += max(0, int(end_token) - start_year)
            else:
                total += max(1, 2026 - start_year)
        return round(min(total, 30.0), 1)

    years = sorted({int(year) for year in _YEAR_PATTERN.findall(normalized_text)})
    if len(years) >= 2:
        return round(min(years[-1] - years[0], 30), 1)
    if years:
        return 1.0
    return 0.0


def parse_cv_text_locally(cv_text: str) -> dict:
    raw_lines = [line.strip() for line in cv_text.splitlines() if line.strip()]
    normalized_text = _normalize(cv_text)
    email_match = _EMAIL_PATTERN.search(cv_text)
    phone_match = _PHONE_PATTERN.search(cv_text)
    email = email_match.group(0) if email_match else ""
    phone = phone_match.group(0) if phone_match else ""

    return {
        "full_name": _extract_name(raw_lines, email),
        "email": email,
        "phone": phone,
        "location": _extract_location(raw_lines, cv_text),
        "summary": " ".join(raw_lines[:3])[:500],
        "skills_technical": _extract_skills(normalized_text),
        "skills_soft": _extract_soft_skills(normalized_text),
        "languages": _extract_languages(normalized_text),
        "certifications": _extract_certifications(raw_lines, normalized_text),
        "education": _extract_education(raw_lines, normalized_text),
        "experience": _extract_experience(raw_lines, normalized_text),
        "projects": _extract_projects(raw_lines, normalized_text),
        "teaching_signals": _extract_teaching_signals(normalized_text),
        "mentoring_signals": _extract_mentoring_signals(normalized_text),
        "youth_education_signals": _extract_youth_signals(normalized_text),
        "estimated_years_experience": _estimate_experience_years(normalized_text),
    }


def _detect_speciality(text: str) -> str:
    lowered = _normalize(text)
    speciality_scores = {speciality: 0 for speciality in TECH_SPECIALITY_HINTS}
    for speciality, hints in TECH_SPECIALITY_HINTS.items():
        speciality_scores[speciality] = sum(1 for hint in hints if _normalize(hint) in lowered)

    priority_order = _load_json_list("speciality_rules.json", list(TECH_SPECIALITY_HINTS.keys()))
    ranked = sorted(
        speciality_scores.items(),
        key=lambda item: (
            item[1],
            -(priority_order.index(item[0]) if item[0] in priority_order else len(priority_order)),
        ),
        reverse=True,
    )
    best = ranked[0][0] if ranked else "Web Dev"
    return best if speciality_scores.get(best, 0) > 0 else "Web Dev"


def _extract_required_skills(normalized_text: str) -> list[str]:
    skills = []
    for speciality_skills in TECH_SPECIALITY_HINTS.values():
        for skill in speciality_skills:
            normalized_skill = _normalize(skill)
            if normalized_skill in _NON_TECHNICAL_HINTS:
                continue
            if _skill_present(normalized_text, skill):
                skills.append(skill)
    return _unique_preserve_order(skills)


def _extract_requirement_lines(requirement_text: str) -> list[str]:
    return [line.strip() for line in requirement_text.splitlines() if line.strip()]


def parse_requirement_text_locally(requirement_text: str, input_mode: str) -> dict:
    normalized_text = _normalize(requirement_text)
    lines = _extract_requirement_lines(requirement_text)
    required_skills = _extract_required_skills(normalized_text)
    preferred_skills: list[str] = []

    for line in lines:
        lowered = _normalize(line)
        if any(marker in lowered for marker in ["preferred", "nice to have", "bonus", "souhait", "souhaite", "desired"]):
            preferred_skills.extend(_extract_required_skills(lowered))

    soft_skills = _extract_soft_skills(normalized_text)
    languages_required = _extract_languages(normalized_text)
    experience_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|ans?)", normalized_text)
    experience_required_years = float(experience_match.group(1)) if experience_match else 0.0
    teaching_required = any(term in normalized_text for term in ["teaching", "tutoring", "trainer", "education", "pedagogy", "enseignement"])
    mentoring_preferred = any(term in normalized_text for term in ["mentor", "mentoring", "coaching", "accompagnement"])
    audience_type = ""
    if any(term in normalized_text for term in ["children", "kids", "young", "teen", "adolescent"]):
        audience_type = "children/teens"
    elif any(term in normalized_text for term in ["adult", "professional", "corporate"]):
        audience_type = "adults"

    responsibilities = [
        line.strip("-•*\t ")
        for line in lines
        if any(term in _normalize(line) for term in ["responsibil", "mission", "role", "duty", "teach", "develop", "build", "design", "maintain"])
    ][:12]

    job_title = lines[0] if lines else ""
    if not job_title and requirement_text.strip():
        job_title = requirement_text.strip().splitlines()[0][:120]

    return {
        "input_mode": input_mode,
        "job_title": job_title[:120],
        "contract_type": "",
        "location": _extract_location(lines, requirement_text),
        "target_sector": "IT / e-learning",
        "required_speciality": _detect_speciality(requirement_text),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "soft_skills": soft_skills,
        "languages_required": languages_required,
        "experience_required_years": experience_required_years,
        "education_requirements": [
            line.strip("-•*\t ")
            for line in lines
            if any(term in _normalize(line) for term in ["degree", "master", "bachelor", "licence", "diploma", "certificate", "education", "formation"])
        ][:8],
        "teaching_required": teaching_required,
        "mentoring_preferred": mentoring_preferred,
        "audience_type": audience_type,
        "responsibilities": responsibilities,
        "keywords": _unique_preserve_order(required_skills + preferred_skills + soft_skills + languages_required),
        "priority_criteria": _unique_preserve_order([skill for skill in required_skills[:6]] + ([job_title] if job_title else [])),
    }