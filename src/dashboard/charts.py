from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_score_gauge(score: float):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Final Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "steps": [
                    {"range": [0, 55], "color": "#ffcccc"},
                    {"range": [55, 70], "color": "#ffe9b3"},
                    {"range": [70, 85], "color": "#d9f2d9"},
                    {"range": [85, 100], "color": "#b3e6b3"},
                ],
            },
        )
    )
    fig.update_layout(height=320)
    return fig


def build_subscores_bar(weighted_scores: dict):
    df = pd.DataFrame({
        "criterion": list(weighted_scores.keys()),
        "score": list(weighted_scores.values()),
    })
    fig = px.bar(df, x="criterion", y="score", title="Weighted Subscores")
    fig.update_layout(height=360, xaxis_title="", yaxis_title="Points")
    return fig


def build_skills_chart(skill_result: dict):
    matched = len(skill_result.get("matched_required", [])) + len(skill_result.get("matched_preferred", []))
    missing = len(skill_result.get("missing_required", [])) + len(skill_result.get("missing_preferred", []))
    df = pd.DataFrame({"category": ["Matched", "Missing"], "count": [matched, missing]})
    fig = px.pie(df, names="category", values="count", title="Skills Coverage")
    fig.update_layout(height=320)
    return fig
