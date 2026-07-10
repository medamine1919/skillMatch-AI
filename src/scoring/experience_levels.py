"""
Niveaux d'expérience professionnelle.

Ce module centralise la détection des niveaux d'expérience à partir de texte
libre ou d'un nombre d'années. Il est utilisé pour comparer l'exigence du
poste avec le niveau estimé du CV.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from src.scoring.synonyms import term_in_text, text_contains_term


@dataclass(frozen=True)
class ExperienceLevel:
    key: str
    label: str
    aliases: tuple[str, ...]
    min_years: float
    max_years: float | None
    rank: int


EXPERIENCE_LEVELS: tuple[ExperienceLevel, ...] = (
    ExperienceLevel(
        key="junior",
        label="Junior / Débutant",
        aliases=(
            "junior", "jr", "jnr", "entry level", "entry-level", "beginner", "beginning",
            "fresher", "fresh graduate", "freshgraduate", "new graduate", "newly graduated",
            "graduate", "first experience", "first job", "débutant", "debutant",
            "jeune diplômé", "jeune diplome", "stagiaire", "internship", "intern",
            "apprentice", "apprenti", "alternant", "starter", "early career",
        ),
        min_years=0.0,
        max_years=2.0,
        rank=1,
    ),
    ExperienceLevel(
        key="mid",
        label="Intermédiaire / Confirmé",
        aliases=(
            "mid-level", "mid level", "intermediate", "confirmed", "confirmé", "confirme",
            "experienced", "experience", "professional", "associate", "expérimenté",
            "2-5 years", "2 to 5 years", "2 years experience", "3 years experience",
            "4 years experience", "mid", "experienced profile", "niveau intermédiaire",
        ),
        min_years=2.0,
        max_years=5.0,
        rank=2,
    ),
    ExperienceLevel(
        key="senior",
        label="Senior",
        aliases=(
            "senior", "sr", "snr", "highly experienced", "expert", "advanced",
            "seasoned", "senior-level", "senior level", "lead contributor", "sénior",
            "senior profile", "5+ years", "7+ years", "8+ years", "10+ years",
            "more than 10 years", "over 10 years",
        ),
        min_years=5.0,
        max_years=None,
        rank=3,
    ),
    ExperienceLevel(
        key="lead",
        label="Lead / Principal",
        aliases=(
            "lead", "technical lead", "tech lead", "team lead", "principal engineer",
            "principal consultant", "principal", "staff engineer", "lead engineer",
            "lead developer", "chef de projet technique", "référent technique", "responsable technique",
        ),
        min_years=7.0,
        max_years=None,
        rank=4,
    ),
    ExperienceLevel(
        key="management",
        label="Management",
        aliases=(
            "manager", "engineering manager", "project manager", "product manager",
            "head of", "director", "vp", "vice president", "executive", "head",
            "head of engineering", "head of department", "engineering lead manager",
            "managerial", "manager de", "directeur", "directrice", "dir", "cto", "cpo",
        ),
        min_years=8.0,
        max_years=None,
        rank=5,
    ),
)

LEVEL_BY_KEY = {level.key: level for level in EXPERIENCE_LEVELS}

_YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:\+|plus|plus de|minimum|min|at least|au moins)?\s*(?:an|ans|année|années|year|years)", re.IGNORECASE)
_RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|to|à|au|between)\s*(\d+(?:\.\d+)?)\s*(?:an|ans|année|années|year|years)", re.IGNORECASE)


def _clean(text: str) -> str:
    return (text or "").strip().lower()


def normalize_years(value: float | int | None) -> float:
    try:
        return max(0.0, float(value or 0.0))
    except Exception:
        return 0.0


def detect_level_from_years(years: float | int | None) -> ExperienceLevel:
    years_value = normalize_years(years)
    if years_value >= 8:
        return LEVEL_BY_KEY["management"]
    if years_value >= 7:
        return LEVEL_BY_KEY["lead"]
    if years_value >= 5:
        return LEVEL_BY_KEY["senior"]
    if years_value >= 2:
        return LEVEL_BY_KEY["mid"]
    return LEVEL_BY_KEY["junior"]


def detect_level_from_text(text: str) -> ExperienceLevel:
    lowered = _clean(text)
    if not lowered:
        return LEVEL_BY_KEY["junior"]

    # Priorité aux rôles de management et de lead.
    # text_contains_term tolère les fautes de frappe (ex: "jinior" -> junior).
    for key in ("management", "lead", "senior", "mid", "junior"):
        level = LEVEL_BY_KEY[key]
        if any(text_contains_term(lowered, _clean(alias)) for alias in level.aliases):
            return level

    years = extract_years_hint(lowered)
    if years is not None:
        return detect_level_from_years(years)

    return LEVEL_BY_KEY["junior"]


def extract_years_hint(text: str) -> float | None:
    lowered = _clean(text)
    if not lowered:
        return None

    range_match = _RANGE_RE.search(lowered)
    if range_match:
        start = float(range_match.group(1))
        end = float(range_match.group(2))
        return max(start, end)

    year_match = _YEARS_RE.search(lowered)
    if year_match:
        return float(year_match.group(1))

    if any(marker in lowered for marker in ("0-1", "0 à 1", "1-2", "2-3", "3-5", "5+", "10+")):
        if "10+" in lowered:
            return 10.0
        if "5+" in lowered:
            return 5.0
        if "3-5" in lowered:
            return 5.0
        if "2-3" in lowered:
            return 3.0
        if "1-2" in lowered:
            return 2.0
        if "0-1" in lowered or "0 à 1" in lowered:
            return 1.0

    return None


def describe_level(level: ExperienceLevel) -> str:
    return level.label


def compare_levels(required: ExperienceLevel, candidate: ExperienceLevel) -> float:
    """Retourne un score de compatibilité entre 0 et 1.

    - même niveau : 1.0
    - candidat au-dessus du niveau requis : 1.0
    - un niveau d'écart : 0.75
    - deux niveaux d'écart : 0.45
    - trois niveaux ou plus : 0.2
    """
    delta = candidate.rank - required.rank
    if delta >= 0:
        return 1.0
    if delta == -1:
        return 0.75
    if delta == -2:
        return 0.45
    return 0.2


def level_keywords(level: ExperienceLevel) -> tuple[str, ...]:
    return level.aliases


def compare_level_to_years(level_key: str, years: float | int | None) -> float:
    """Adéquation (0..1) entre un nombre d'`years` et le niveau `level_key`.

    - années dans la fourchette [min_years, max_years] du niveau : 1.0
    - en dessous du minimum : proportionnel (years / min_years)
    - au-dessus du maximum (surqualifié) : 1.0
    """
    level = LEVEL_BY_KEY.get(level_key)
    y = normalize_years(years)
    if level is None:
        return min(1.0, y / 5.0) if y else 0.0
    lo = level.min_years
    hi = level.max_years
    if y >= lo and (hi is None or y <= hi):
        return 1.0
    if y < lo:
        return round(max(0.0, y / lo), 3) if lo > 0 else 1.0
    return 1.0
