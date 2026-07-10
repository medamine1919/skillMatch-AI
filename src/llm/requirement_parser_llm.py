from __future__ import annotations

from src.parsing.local_parsers import parse_requirement_text_locally
from src.llm.groq_client import GroqClientWrapper
from src.llm.prompts import build_requirement_parsing_prompt
from src.parsing.validators import validate_requirement_json
from src.utils import extract_json_from_text


def parse_requirement_with_llm(requirement_text: str, input_mode: str) -> dict:
    try:
        client = GroqClientWrapper()
        prompt = build_requirement_parsing_prompt(requirement_text, input_mode=input_mode)
        raw = client.complete(prompt=prompt, temperature=0.1)
        parsed = extract_json_from_text(raw)
        return validate_requirement_json(parsed)
    except Exception:
        local = parse_requirement_text_locally(requirement_text, input_mode=input_mode)
        return validate_requirement_json(local)
