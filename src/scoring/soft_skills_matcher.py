"""
Matching des SOFT SKILLS — même logique ATS que les compétences techniques :
    Note = 0.85 × couverture des soft skills EXIGÉS
         + 0.15 × bonus soft skills EN PLUS reconnus (plafonné)

Le matching et la reconnaissance s'appuient sur le DICTIONNAIRE (terms_equivalent)
pour gérer FR/EN et variantes ("travail d'équipe" ≡ "teamwork", etc.).
"""
from __future__ import annotations

from rapidfuzz import fuzz

from src.scoring.synonyms import terms_equivalent, expand_term

COVERAGE_WEIGHT = 0.85
BONUS_WEIGHT = 0.15
BONUS_FULL = 3.0

# Vocabulaire des soft skills reconnus (clés du dictionnaire). Un soft skill
# "en plus" ne donne un bonus que s'il appartient à ce vocabulaire.
_SOFT_KEYS = [
    "communication", "equipe", "teamwork", "leadership", "autonomie",
    "creativite", "rigueur", "adaptabilite", "organisation", "resolution",
    "polyvalence", "proactivite", "empathie", "curiosite",
]
# On déplie chaque clé en toutes ses variantes pour reconnaître un large éventail.
_SOFT_VOCAB: list[str] = []
for _k in _SOFT_KEYS:
    _SOFT_VOCAB += expand_term(_k)


def _fuzzy(a: str, b: str) -> float:
    a, b = a.lower(), b.lower()
    return max(fuzz.ratio(a, b), fuzz.token_set_ratio(a, b)) / 100.0


def _matches(term: str, candidates: list[str]) -> bool:
    return any(terms_equivalent(term, c) or _fuzzy(term, c) >= 0.75 for c in candidates)


def compute_soft_skill_match(candidate_soft_skills: list[str], required_soft_skills: list[str]) -> dict:
    cand = candidate_soft_skills or []
    required = required_soft_skills or []

    # --- Aucun soft skill exigé : on valorise seulement la présence réelle
    #     de soft skills dans le CV. Plus il y en a, plus la note monte. ---
    if not required:
        ratio = min(len(cand) / 5.0, 1.0) if cand else 0.0
        return {"ratio": ratio, "matched": cand[:5], "missing": [], "extra_relevant": []}

    # --- Couverture des soft skills demandés ---
    matched = [s for s in required if _matches(s, cand)]
    missing = [s for s in required if s not in matched]
    coverage = len(matched) / len(required)

    # --- Bonus : soft skills EN PLUS reconnus (hors ceux déjà demandés) ---
    extras = [c for c in cand if not any(terms_equivalent(c, s) or _fuzzy(c, s) >= 0.75 for s in required)]
    relevant_extra = [c for c in extras if any(terms_equivalent(c, v) for v in _SOFT_VOCAB)]
    bonus_fraction = min(1.0, len(relevant_extra) / BONUS_FULL)

    ratio = max(0.0, min(1.0, COVERAGE_WEIGHT * coverage + BONUS_WEIGHT * bonus_fraction))
    return {"ratio": ratio, "matched": matched, "missing": missing, "extra_relevant": relevant_extra}
