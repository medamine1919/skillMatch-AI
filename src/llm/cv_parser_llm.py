from __future__ import annotations

import json

from src.llm.groq_client import GroqClientWrapper
from src.llm.prompts import build_cv_parsing_prompt
from src.parsing.local_parsers import parse_cv_text_locally
from src.parsing.validators import validate_cv_json
from src.utils import extract_json_from_text


def parse_cv_with_llm(cv_text: str) -> dict:
    try:
        client = GroqClientWrapper()
        prompt = build_cv_parsing_prompt(cv_text)
        raw = client.complete(prompt=prompt, temperature=0.1)
        parsed = extract_json_from_text(raw)
        return validate_cv_json(parsed)
    except Exception as e:
        local = parse_cv_text_locally(cv_text)
        try:
            return validate_cv_json(local)
        except Exception:
            raise ValueError(
                f"CV parsing validation failed: {str(e)}. "
                f"Local fallback response was: {json.dumps(local, indent=2, ensure_ascii=False)}"
            ) from e
