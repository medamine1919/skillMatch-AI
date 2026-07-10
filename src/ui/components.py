from __future__ import annotations

import streamlit as st


def score_badge(score: float) -> str:
    if score >= 85:
        return "🟢 Excellent"
    if score >= 70:
        return "🟩 Strong"
    if score >= 55:
        return "🟨 Moderate"
    return "🟥 Weak"


def section_header(title: str) -> None:
    st.markdown(f"### {title}")
