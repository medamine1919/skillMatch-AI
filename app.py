from __future__ import annotations

import streamlit as st

from src.config import (
    APP_NAME,
    COMPANY_NAME,
    DEFAULT_LANGUAGE,
    GROQ_API_KEY,
    ensure_directories,
)
from src.db.schema import initialize_database
from src.i18n import t
from src.ui.upload_page import render_upload_page
from src.ui.results_page import render_results_page
from src.ui.dashboard_page import render_dashboard_page


def bootstrap() -> None:
    ensure_directories()
    initialize_database()


def initialize_session() -> None:
    if "lang" not in st.session_state:
        st.session_state["lang"] = DEFAULT_LANGUAGE
    if "analysis_result" not in st.session_state:
        st.session_state["analysis_result"] = None
    if "page" not in st.session_state:
        st.session_state["page"] = "upload"


def apply_ui_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --sky-50: #f0f9ff;
            --sky-100: #e0f2fe;
            --sky-200: #bae6fd;
            --sky-500: #0ea5e9;
            --sky-700: #0369a1;
        }

        .stApp {
            background: linear-gradient(165deg, var(--sky-50) 0%, #ffffff 40%, var(--sky-100) 100%);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--sky-100) 0%, #f8fbff 100%);
            border-right: 1px solid var(--sky-200);
        }

        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid var(--sky-200);
            border-radius: 12px;
            padding: 12px;
        }

        .rh-banner {
            background: linear-gradient(120deg, #e0f2fe 0%, #f0f9ff 100%);
            border: 1px solid var(--sky-200);
            border-left: 6px solid var(--sky-500);
            color: #0c4a6e;
            border-radius: 12px;
            padding: 14px 16px;
            margin: 6px 0 16px 0;
        }

        .rh-banner strong {
            color: var(--sky-700);
            display: block;
            margin-bottom: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    bootstrap()
    initialize_session()
    apply_ui_theme()

    lang = st.session_state["lang"]

    with st.sidebar:
        st.title(APP_NAME)
        st.caption(COMPANY_NAME)

        chosen_lang = st.selectbox(
            t("language", lang),
            options=["fr", "en"],
            index=0 if lang == "fr" else 1,
        )
        st.session_state["lang"] = chosen_lang
        lang = chosen_lang

        if GROQ_API_KEY:
            st.success(t("status_ready", lang))
        else:
            st.error(t("status_missing_key", lang))

        page = st.radio(
            "Navigation",
            options=["upload", "results", "dashboard"],
            format_func=lambda x: {
                "upload": "Upload / Analyze",
                "results": t("results", lang),
                "dashboard": t("dashboard", lang),
            }.get(x, x),
            index=["upload", "results", "dashboard"].index(st.session_state.get("page", "upload")),
        )
        st.session_state["page"] = page

    st.title(f"{APP_NAME} · {COMPANY_NAME}")

    if st.session_state["page"] == "upload":
        render_upload_page(lang=lang)
    elif st.session_state["page"] == "results":
        render_results_page(lang=lang)
    else:
        render_dashboard_page(lang=lang)


if __name__ == "__main__":
    main()
