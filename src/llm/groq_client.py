from __future__ import annotations

from pathlib import Path

from groq import Groq

from src.config import GROQ_API_KEY, GROQ_MODEL


class GroqClientWrapper:
    def __init__(self) -> None:
        if not GROQ_API_KEY:
            env_path = Path(__file__).resolve().parent.parent.parent / ".env"
            raise ValueError(
                f"GROQ_API_KEY is missing. Add it to {env_path}."
            )
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL

    def complete(self, prompt: str, temperature: float = 0.1) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise HR and CV analysis assistant. Always follow the requested JSON schema exactly.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
        return response.choices[0].message.content or ""
