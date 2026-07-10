from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


_EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
_PHONE_CANDIDATE_PATTERN = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
_YEAR_RANGE_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}\s*(?:-|to|a|au|/)\s*(?:present|current|now|aujourdhui|(?:19|20)\d{2})\b",
    flags=re.IGNORECASE,
)
_YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")

_CV_SECTION_KEYWORDS = (
    "curriculum vitae",
    "resume",
    "profil",
    "profile",
    "summary",
    "about me",
    "experience",
    "professional experience",
    "work experience",
    "experience professionnelle",
    "employment",
    "skills",
    "competences",
    "education",
    "formation",
    "certifications",
    "projects",
    "projets",
    "languages",
    "langues",
)

_JOB_OFFER_KEYWORDS = (
    "we are looking for",
    "looking for",
    "job description",
    "responsibilities",
    "requirements",
    "apply now",
    "join our team",
    "about the company",
    "benefits",
    "offre d emploi",
    "nous recherchons",
    "poste a pourvoir",
    "profil recherche",
    "missions principales",
    "type de contrat",
    "salaire",
)

_NON_CV_CONTENT_KEYWORDS = (
    "liste des projets",
    "projet 1",
    "projet 2",
    "nombre de seances",
    "composants",
    "chapitre",
    "module",
    "broche",
    "arduino",
    "invoice",
    "facture",
    "report",
    "rapport",
    "memo",
    "note de service",
    "meeting minutes",
    "agenda",
    "brochure",
    "catalog",
    "catalogue",
)

_PLACEHOLDER_VALUES = {
    "n/a",
    "na",
    "none",
    "unknown",
    "not provided",
    "non renseigne",
    "candidate",
}


@dataclass(frozen=True)
class CVValidationResult:
    is_cv: bool
    confidence: float
    score: int
    reasons: list[str]


def _normalize_text(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.lower().split())


def _contains_phone_number(text: str) -> bool:
    for candidate in _PHONE_CANDIDATE_PATTERN.findall(text):
        digits = re.sub(r"\D", "", candidate)
        if 8 <= len(digits) <= 15:
            return True
    return False


def _keyword_hits(normalized_text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for keyword in keywords if keyword in normalized_text)


def _confidence_from_score(score: int, min_score: int = -4, max_score: int = 8) -> float:
    if score <= min_score:
        return 0.0
    if score >= max_score:
        return 1.0
    return round((score - min_score) / (max_score - min_score), 2)


def _is_meaningful(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered:
        return False
    return lowered not in _PLACEHOLDER_VALUES


def validate_cv_text(raw_text: str) -> CVValidationResult:
    normalized_text = _normalize_text(raw_text)
    word_count = len(normalized_text.split())

    if not normalized_text:
        return CVValidationResult(
            is_cv=False,
            confidence=0.0,
            score=-5,
            reasons=["empty_text"],
        )

    has_email = bool(_EMAIL_PATTERN.search(raw_text))
    has_phone = _contains_phone_number(raw_text)
    section_hits = _keyword_hits(normalized_text, _CV_SECTION_KEYWORDS)
    job_offer_hits = _keyword_hits(normalized_text, _JOB_OFFER_KEYWORDS)
    non_cv_content_hits = _keyword_hits(normalized_text, _NON_CV_CONTENT_KEYWORDS)
    date_range_hits = len(_YEAR_RANGE_PATTERN.findall(normalized_text))
    year_hits = len(_YEAR_PATTERN.findall(normalized_text))

    has_contact = has_email or has_phone
    has_core_cv_section = any(
        keyword in normalized_text
        for keyword in (
            "experience",
            "education",
            "formation",
            "skills",
            "competences",
            "projects",
            "projets",
            "summary",
            "resume",
            "profile",
            "profil",
        )
    )

    score = 0
    reasons: list[str] = []

    if has_email:
        score += 2
    if has_phone:
        score += 1
    if not has_contact:
        reasons.append("missing_contact")

    if section_hits >= 4:
        score += 3
    elif section_hits >= 2:
        score += 2
    elif section_hits == 1:
        score += 1
    else:
        reasons.append("missing_cv_sections")

    if date_range_hits >= 1 or year_hits >= 3:
        score += 2
    elif year_hits >= 1:
        score += 1
    else:
        reasons.append("missing_timeline")

    if word_count < 60:
        score -= 2
        reasons.append("too_short")

    if job_offer_hits >= 4:
        score -= 5
        reasons.append("job_offer_signals")
    elif job_offer_hits >= 2:
        score -= 3
        reasons.append("job_offer_signals")
    elif job_offer_hits == 1:
        score -= 1

    if non_cv_content_hits >= 4 and not (has_email or has_phone):
        score -= 4
        reasons.append("non_cv_content_signals")
    elif non_cv_content_hits >= 2 and not (has_email or has_phone):
        score -= 2
        reasons.append("non_cv_content_signals")

    if word_count > 2500 and not (has_email or has_phone):
        score -= 3
        reasons.append("unusual_length_without_identity")

    if non_cv_content_hits >= 2:
        score -= 2
        reasons.append("generic_document_signals")

    if has_contact and not has_core_cv_section:
        score -= 2
        reasons.append("missing_core_cv_structure")

    core_signals = 0
    if has_contact:
        core_signals += 1
    if section_hits >= 2:
        core_signals += 1
    if date_range_hits >= 1 or year_hits >= 2:
        core_signals += 1

    is_cv = score >= 4 and core_signals >= 2 and has_core_cv_section

    if job_offer_hits >= 4 and not has_contact:
        is_cv = False

    if non_cv_content_hits >= 2 and not has_core_cv_section:
        is_cv = False

    return CVValidationResult(
        is_cv=is_cv,
        confidence=_confidence_from_score(score),
        score=score,
        reasons=reasons,
    )


def validate_parsed_cv_data(cv_data: dict) -> CVValidationResult:
    full_name = str(cv_data.get("full_name", "")).strip()
    email = str(cv_data.get("email", "")).strip()
    phone = str(cv_data.get("phone", "")).strip()

    technical_skills = [s for s in cv_data.get("skills_technical", []) if str(s).strip()]
    soft_skills = [s for s in cv_data.get("skills_soft", []) if str(s).strip()]

    experience_count = 0
    for exp in cv_data.get("experience", []):
        if not isinstance(exp, dict):
            continue
        if any(
            str(exp.get(field, "")).strip()
            for field in ("job_title", "company", "description", "start_date", "end_date")
        ):
            experience_count += 1

    education_count = 0
    for edu in cv_data.get("education", []):
        if not isinstance(edu, dict):
            continue
        if any(str(edu.get(field, "")).strip() for field in ("degree", "field", "institution")):
            education_count += 1

    project_count = len([p for p in cv_data.get("projects", []) if str(p).strip()])

    has_identity = _is_meaningful(full_name) or bool(_EMAIL_PATTERN.search(email)) or _contains_phone_number(phone)

    score = 0
    reasons: list[str] = []

    if has_identity:
        score += 2
    else:
        reasons.append("missing_identity")

    skill_count = len(technical_skills) + len(soft_skills)
    if skill_count >= 6:
        score += 2
    elif skill_count >= 2:
        score += 1
    else:
        reasons.append("missing_skills")

    if experience_count >= 1:
        score += 2
    else:
        reasons.append("missing_experience")

    if education_count >= 1:
        score += 1
    if project_count >= 1:
        score += 1

    if not has_identity and experience_count == 0 and education_count == 0:
        score -= 4

    core_signals = 0
    if has_identity:
        core_signals += 1
    if skill_count >= 2:
        core_signals += 1
    if experience_count >= 1 or education_count >= 1:
        core_signals += 1

    is_cv = score >= 3 and core_signals >= 2

    return CVValidationResult(
        is_cv=is_cv,
        confidence=_confidence_from_score(score),
        score=score,
        reasons=reasons,
    )
