from __future__ import annotations

from typing import List

from pydantic import ValidationError

from src.parsing.schema_models import CVSchema, RequirementSchema


def _build_error(loc: List[str], msg: str, err_type: str = "value_error"):
    return {"loc": tuple(loc), "msg": msg, "type": err_type}


def validate_cv_json(data: dict) -> dict:
    # First, let pydantic coerce/parse defaults
    model = CVSchema.model_validate(data)
    result = model.model_dump()

    # Now apply stricter domain checks: ensure the parsed document looks like a CV
    errors = []

    # Identification: require either a non-empty full_name or an email-like value
    full_name = (result.get("full_name") or "").strip()
    email = (result.get("email") or "").strip()
    if not full_name and not email:
        errors.append(_build_error(["full_name"], "Le CV doit contenir au moins un nom ou un email"))

    # Content: require at least skills or experience or education
    skills = result.get("skills_technical") or []
    experience = result.get("experience") or []
    education = result.get("education") or []
    if not skills and not experience and not education:
        errors.append(_build_error(["skills_technical"], "Le CV ne contient pas d'informations exploitables (compétences, expérience ou formation)"))

    if errors:
        raise ValidationError(errors, CVSchema)

    return result


def validate_requirement_json(data: dict) -> dict:
    model = RequirementSchema.model_validate(data)
    return model.model_dump()


def is_likely_cv_text(text: str) -> (bool, list):
    """Heuristique simple pour estimer si un texte provient d'un CV.

    Retourne (True, []) si probablement CV, sinon (False, [raisons]).
    """
    if not text or not isinstance(text, str):
        return False, ["Texte vide ou invalide"]

    lower = text.lower()
    reasons: list = []

    # Vérifier présence d'un contact: email ou téléphone
    import re
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.[a-z]{2,}", lower)
    phone_match = re.search(r"(\+?\d[\d\s\-\(\)]{6,}\d)", lower)
    if not email_match and not phone_match:
        reasons.append("Aucune adresse e-mail ni numéro de téléphone détecté")

    # Rechercher mots-clés de sections CV (au moins 2)
    keywords = [
        "experience",
        "education",
        "formation",
        "compétence",
        "compétences",
        "skills",
        "resume",
        "curriculum",
        "profil",
        "expérience",
        "éducation",
    ]
    found = sum(1 for kw in keywords if kw in lower)
    if found < 2:
        reasons.append("Peu d'indications de sections CV (compétences/expérience/formation)")

    # Longueur minimale raisonnable
    if len(lower) < 200:
        reasons.append("Texte extrait trop court pour être un CV")

    return (len(reasons) == 0, reasons)
