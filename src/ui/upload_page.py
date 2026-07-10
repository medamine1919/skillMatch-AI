from __future__ import annotations

import traceback
from pathlib import Path

import streamlit as st

from src.config import EXPORTS_DIR
from src.db.repository import save_analysis
from src.export.csv_exporter import export_result_to_csv
from src.i18n import t
from src.ingestion.file_handler import save_uploaded_file
from src.ingestion.text_extractor import extract_text
from src.llm.cv_parser_llm import parse_cv_with_llm
from src.llm.requirement_parser_llm import parse_requirement_with_llm
from src.parsing.normalizers import normalize_cv_data, normalize_requirement_data
from src.parsing.cv_document_validator import validate_cv_text, validate_parsed_cv_data
from src.scoring.explanation_engine import build_detailed_explanation, build_short_explanation
from src.scoring.scoring_engine import compute_scoring


def render_upload_page(lang: str = "fr") -> None:
    st.subheader("Upload & Analyze")
    st.markdown(
        f"""
        <div class="rh-banner">
            <strong>{t("rh_analysis_title", lang)}</strong>
            <span>{t("rh_analysis_text", lang)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader(
            label=t("upload_cv", lang),
            type=["pdf", "docx"],
            help=t("upload_help", lang),
        )

    with col2:
        mode_label_map = {
            "free_need": t("free_need", lang),
            "job_offer": t("job_offer", lang),
        }
        input_mode = st.selectbox(
            t("need_mode", lang),

    requirement_text = st.text_area(
        label=t("need_input", lang),
        height=220,
        placeholder=(
            "Example: We are looking for a web development tutor able to teach HTML, CSS, JavaScript to teenagers..."
            if lang == "en"
            else "Exemple : Nous recherchons un tuteur en développement web capable d'enseigner HTML, CSS, JavaScript à des adolescents..."
        ),
    )

    analyze_clicked = st.button(t("analyze", lang), type="primary", use_container_width=True)

    if analyze_clicked:
        if not GROQ_API_KEY:
            st.error("GROQ_API_KEY is missing. Add it to .env (or Streamlit secrets) and restart the app.")
            return
        if uploaded_file is None:
            st.error("Please upload a CV first.")
                    req_data = parse_requirement_with_llm(requirement_text, input_mode=input_mode) if requirement_text.strip() else {}
        if not requirement_text.strip():
            st.error("Please enter a hiring need or a job offer.")
            return

        try:
            with st.spinner("Running analysis..."):
                saved_path = save_uploaded_file(uploaded_file)
                raw_text = extract_text(saved_path)

                if not raw_text.strip():
                    raise ValueError("No text could be extracted from the uploaded document.")

                text_validation = validate_cv_text(raw_text)
                if not text_validation.is_cv:
                    raise ValueError(t("invalid_cv_document", lang))

                cv_data = parse_cv_with_llm(raw_text)
                cv_data = normalize_cv_data(cv_data)

                parsed_validation = validate_parsed_cv_data(cv_data)
                if not parsed_validation.is_cv:
                    raise ValueError(t("invalid_cv_document", lang))

                req_data = parse_requirement_with_llm(requirement_text, input_mode=input_mode)
                req_data = normalize_requirement_data(req_data)

                result = compute_scoring(cv_data=cv_data, req_data=req_data)
                result["short_explanation"] = build_short_explanation(result)
                result["detailed_explanation"] = build_detailed_explanation(cv_data, req_data, result)

                base_name = Path(saved_path).stem
                csv_path = export_result_to_csv(EXPORTS_DIR / f"{base_name}_result.csv", cv_data, req_data, result)

                analysis_id = save_analysis(
                    file_name=uploaded_file.name,
                    input_mode=input_mode,
                    raw_requirement=requirement_text,
                    cv_json=cv_data,
                    requirement_json=req_data,
                    result_json=result,
                )

                st.session_state["analysis_result"] = {
                    "analysis_id": analysis_id,
                    "file_name": uploaded_file.name,
                    "saved_path": str(saved_path),
                    "cv_data": cv_data,
                    "requirement_data": req_data,
                    "result": result,
                    "csv_export_path": str(csv_path),
                }
                st.session_state["page"] = "results"
                st.success(t("analysis_complete", lang))
                st.rerun()

        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            st.code(traceback.format_exc())
