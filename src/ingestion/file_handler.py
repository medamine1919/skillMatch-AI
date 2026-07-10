from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from src.config import MAX_FILE_SIZE_MB, SUPPORTED_FILE_TYPES, UPLOADS_DIR
from src.utils import generate_safe_filename, validate_filename_pattern


def validate_uploaded_file(uploaded_file) -> None:
    # Validate filename pattern first (fail-fast)
    validate_filename_pattern(uploaded_file.name)
    
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in SUPPORTED_FILE_TYPES:
        raise ValueError(f"Unsupported file type: {extension}. Allowed: {SUPPORTED_FILE_TYPES}")

    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File is too large ({size_mb:.2f} MB). Max allowed is {MAX_FILE_SIZE_MB} MB.")


def save_uploaded_file(uploaded_file) -> Path:
    validate_uploaded_file(uploaded_file)
    safe_name = generate_safe_filename(uploaded_file.name)
    target_path = UPLOADS_DIR / safe_name

    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return target_path
