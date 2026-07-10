from __future__ import annotations

import streamlit as st

from src.config import SCORING_WEIGHTS, SHORTLIST_THRESHOLDS
from src.constants import DECISION_LABELS
from src.i18n import t


CRITERION_LABELS = {
    "speciality_match": {
        "fr": "Correspondance specialite",
        "en": "Speciality match",
    },
    "technical_skills": {
        "fr": "Competences techniques",
        "en": "Technical skills",
    },
    "relevant_experience": {
        "fr": "Experience pertinente",
        "en": "Relevant experience",
    },
    "pedagogy_tutoring": {
        "fr": "Pedagogie / tutorat",
        "en": "Pedagogy / tutoring",
    },
    "soft_skills": {
        "fr": "Competences comportementales",
        "en": "Soft skills",
    },
    "semantic_similarity": {
        "fr": "Similarite semantique",
        "en": "Semantic similarity",
    },
}


def localize_criterion_name(key: str, lang: str) -> str:
    labels = CRITERION_LABELS.get(key, {})
    return labels.get(lang, key)


def render_list(values: list[str], empty_text: str) -> None:
    cleaned = [item.strip() for item in values if str(item).strip()]
    if not cleaned:
        st.caption(empty_text)
        return
    st.markdown("\n".join(f"- {item}" for item in cleaned))


def build_rule_rows(lang: str) -> list[dict]:
    excellent = SHORTLIST_THRESHOLDS["excellent"]
    strong = SHORTLIST_THRESHOLDS["strong"]
    moderate = SHORTLIST_THRESHOLDS["moderate"]

    return [
        {
            t("level", lang): DECISION_LABELS["excellent"],
            t("rule", lang): f"score >= {excellent}",
            t("action", lang): t("action_excellent", lang),
        },
        {
            t("level", lang): DECISION_LABELS["strong"],
            t("rule", lang): f"{strong} <= score < {excellent}",
            t("action", lang): t("action_strong", lang),
        },
        {
            t("level", lang): DECISION_LABELS["moderate"],
            t("rule", lang): f"{moderate} <= score < {strong}",
            t("action", lang): t("action_moderate", lang),
        },
        {
            t("level", lang): DECISION_LABELS["weak"],
            t("rule", lang): f"score < {moderate}",
            t("action", lang): t("action_weak", lang),
        },
    ]


def build_weight_rows(result: dict, lang: str) -> list[dict]:
    weighted_scores = result.get("weighted_scores", {})
    rows = []

    for key, max_weight in SCORING_WEIGHTS.items():
        points = float(weighted_scores.get(key, 0))
        ratio = 0.0 if max_weight == 0 else max(0.0, min(points / max_weight, 1.0))
        rows.append(
            {
                t("criterion", lang): localize_criterion_name(key, lang),
                t("weight_max", lang): max_weight,
                t("points_awarded", lang): round(points, 2),
                t("match_ratio", lang): f"{ratio * 100:.0f}%",
            }
        )

    return rows
