from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any


def generate_safe_filename(original_name: str) -> str:
    path = Path(original_name)
    ext = path.suffix.lower()
    unique_id = uuid.uuid4().hex[:12]
    base_name = re.sub(r"[^a-zA-Z0-9_-]", "_", path.stem)[:40]
    return f"{base_name}_{unique_id}{ext}"


def validate_filename_pattern(filename: str) -> None:
    """
    Validate that the filename looks like a CV filename ending with _cv.
    
    Args:
        filename: The original filename with extension
        
    Raises:
        ValueError: If filename does not match the required pattern
    """
    path = Path(filename)
    # Normalize minor user naming quirks (extra spaces, mixed separators).
    name_without_ext = re.sub(r"\s+", " ", path.stem.strip().lower())

    # Accept real CV names such as "mouhamed_aziz_mejri_cv" or "belhaj_massoud_mohamed_amine_cv".
    # We only require a non-empty prefix and a terminal "cv" token.
    pattern = r'^[a-z0-9]+(?:[ _-][a-z0-9]+)*[ _-]cv$'

    if not re.match(pattern, name_without_ext):
        raise ValueError(
            "Le nom du fichier doit se terminer par cv (ex: mouhamed_aziz_mejri_cv.pdf)."
        )


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_list(values: list[str] | None) -> list[str]:
    if not values:
        return []

    cleaned: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not isinstance(value, str):
            continue
        item = value.strip()
        if not item:
            continue
        key = item.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(item)

    return cleaned


def load_json(filepath: str | Path) -> dict[str, Any]:
    path = Path(filepath)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_json_from_text(text: str) -> dict[str, Any]:
    if not text:
        raise ValueError("Empty text received from LLM.")

    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    # Try fenced code block first
    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    # Try first JSON object
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return json.loads(text[first_brace:last_brace + 1])

    raise ValueError("Could not extract a valid JSON object from LLM output.")


def safe_lower(value: str | None) -> str:
    return (value or "").strip().lower()
