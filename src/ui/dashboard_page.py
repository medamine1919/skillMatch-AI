from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.dashboard.charts import build_score_gauge, build_skills_chart, build_subscores_bar
from src.dashboard.summary_builder import build_declitech_fit_summary
from src.db.repository import list_analyses
from src.i18n import t
from src.ui.components import score_badge, section_header
from src.ui.result_view_helpers import build_rule_rows, build_weight_rows, render_list


def _build_history_rows(history: list[dict], lang: str) -> list[dict]:
    rows: list[dict] = []
    for item in history:
        res = item.get("result", {})
        input_mode = str(item.get("input_mode", ""))
        input_mode_label = t(input_mode, lang) if input_mode in {"free_need", "job_offer"} else input_mode
        rows.append(
            {
                t("created_at", lang): item.get("created_at", ""),
                t("file_name", lang): item.get("file_name", ""),
                t("input_type", lang): input_mode_label,
                t("final_score", lang): res.get("final_score", 0),
                t("decision", lang): res.get("decision_label", ""),
                t("recommendation", lang): res.get("recommendation_label", ""),
                t("speciality", lang): res.get("cv_speciality", ""),
            }
        )
    return rows


def render_dashboard_page(lang: str = "fr") -> None:
    payload = st.session_state.get("analysis_result")

    if payload:
        result = payload["result"]
        cv_data = payload["cv_data"]
        req_data = payload["requirement_data"]
        declitech_fit = build_declitech_fit_summary(cv_data, req_data, result)
        skill_result = result.get("skill_result", {})
        score = float(result.get("final_score", 0))
        semantic_ratio = float(result.get("semantic_similarity_ratio", 0))

        section_header(t("current_analysis", lang))

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(label=t("final_score", lang), value=f"{score:.2f}/100")
        with m2:
            st.metric(label=t("decision", lang), value=result.get("decision_label", "-"))
        with m3:
            st.metric(label=t("recommendation", lang), value=result.get("recommendation_label", "-"))
        with m4:
            st.metric(label=t("semantic_similarity", lang), value=f"{semantic_ratio * 100:.1f}%")

        st.progress(max(0.0, min(score / 100.0, 1.0)))
        st.markdown(score_badge(score))

        c1, c2 = st.columns([1, 1])
        with c1:
            st.plotly_chart(build_score_gauge(score), use_container_width=True)
        with c2:
            st.plotly_chart(build_skills_chart(skill_result), use_container_width=True)

        section_header(t("subscores", lang))
        st.plotly_chart(build_subscores_bar(result.get("weighted_scores", {})), use_container_width=True)
        st.dataframe(build_weight_rows(result, lang), hide_index=True, use_container_width=True)

        section_header(t("decision_rules", lang))
        st.dataframe(build_rule_rows(lang), hide_index=True, use_container_width=True)

        left, right = st.columns([1.2, 0.8])

        with left:
            section_header(t("candidate_info", lang))
            st.markdown(f"**{t('full_name', lang)}**: {cv_data.get('full_name', '-') or '-'}")
            st.markdown(f"**{t('email', lang)}**: {cv_data.get('email', '-') or '-'}")
            st.markdown(f"**{t('phone', lang)}**: {cv_data.get('phone', '-') or '-'}")
            st.markdown(f"**{t('location', lang)}**: {cv_data.get('location', '-') or '-'}")

            section_header(t("parsed_requirement", lang))
            st.markdown(f"**{t('job_title', lang)}**: {req_data.get('job_title', '-') or '-'}")
            st.markdown(
                f"**{t('required_speciality', lang)}**: {req_data.get('required_speciality', '-') or '-'}"
            )
            st.markdown(
                f"**{t('experience_required', lang)}**: {req_data.get('experience_required_years', 0)}"
            )

            skills_left, skills_right = st.columns(2)
            with skills_left:
                section_header(t("matched_skills", lang))
                st.markdown(f"**{t('matched_required', lang)}**")
                render_list(skill_result.get("matched_required", []), t("no_items", lang))
                st.markdown(f"**{t('matched_preferred', lang)}**")
                render_list(skill_result.get("matched_preferred", []), t("no_items", lang))
            with skills_right:
                section_header(t("missing_skills", lang))
                st.markdown(f"**{t('missing_required', lang)}**")
                render_list(skill_result.get("missing_required", []), t("no_items", lang))
                st.markdown(f"**{t('missing_preferred', lang)}**")
                render_list(skill_result.get("missing_preferred", []), t("no_items", lang))

        with right:
            section_header(t("declitech_fit", lang))
            st.info(declitech_fit["summary"])
            st.markdown(f"**{t('declitech_focus', lang)}**")
            render_list(declitech_fit.get("fit_pillars", []), t("no_items", lang))
            st.info(declitech_fit["declitech_focus"])

            section_header(t("short_explanation", lang))
            st.success(result.get("short_explanation", ""))

            csv_path = payload.get("csv_export_path")
            if csv_path and Path(csv_path).exists():
                with open(csv_path, "rb") as f:
                    st.download_button(
                        label=t("export_csv", lang),
                        data=f.read(),
                        file_name=Path(csv_path).name,
                        mime="text/csv",
                        use_container_width=True,
                    )
    else:
        st.info(t("no_result", lang))

    section_header(t("history", lang))
    history = list_analyses(limit=20)
    if not history:
        st.info(t("no_history", lang))
        return

    st.caption(t("history_note", lang))
    st.dataframe(_build_history_rows(history, lang), hide_index=True, use_container_width=True)
