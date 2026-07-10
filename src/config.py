from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Always load environment variables from the project root .env file.
load_dotenv(dotenv_path=BASE_DIR / ".env")
SRC_DIR = BASE_DIR / "src"
DATABASE_DIR = BASE_DIR / "database"
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
EXPORTS_DIR = DATA_DIR / "exports"
TEMP_DIR = DATA_DIR / "temp"
RESOURCES_DIR = BASE_DIR / "resources"
ASSETS_DIR = BASE_DIR / "assets"

DB_PATH = DATABASE_DIR / "cv_scoring.db"

APP_NAME = os.getenv("APP_NAME", "CV Scoring")
COMPANY_NAME = os.getenv("COMPANY_NAME", "DecliTech")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "fr").lower().strip()

SUPPORTED_UI_LANGUAGES = ["fr", "en"]
SUPPORTED_FILE_TYPES = [".pdf", ".docx"]
MAX_FILE_SIZE_MB = 10


def _normalize_secret(value: str) -> str:
    cleaned = value.strip().strip('"').strip("'")
    if not cleaned:
        return ""
    placeholders = {
        "your_real_groq_api_key_here",
        "your_groq_api_key_here",
        "changeme",
    }
    if cleaned.lower() in placeholders:
        return ""
    return cleaned


def _get_secret(name: str, default: str = "") -> str:
    value = _normalize_secret(os.getenv(name, ""))
    if value:
        return value
    try:
        import streamlit as st  # type: ignore[import-not-found]

        secret_value = _normalize_secret(str(st.secrets.get(name, "")))
        if isinstance(secret_value, str):
            return secret_value
    except Exception:
        # Streamlit secrets may be unavailable in non-Streamlit contexts.
        pass
    return default


GROQ_API_KEY = _get_secret("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SCORING_WEIGHTS = {
    "speciality_match": 25,
    "technical_skills": 25,
    "relevant_experience": 15,
    "pedagogy_tutoring": 15,
    "soft_skills": 10,
    "semantic_similarity": 10,
}

SHORTLIST_THRESHOLDS = {
    "excellent": 85,
    "strong": 70,
    "moderate": 55,
    "weak": 0,
}

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

ENABLE_OCR = True
OCR_LANGUAGE = "eng+fra"


def ensure_directories() -> None:
    required_dirs = [
        DATABASE_DIR,
        DATA_DIR,
        UPLOADS_DIR,
        EXPORTS_DIR,
        TEMP_DIR,
        RESOURCES_DIR,
        ASSETS_DIR,
    ]
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)
