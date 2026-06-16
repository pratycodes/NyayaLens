from __future__ import annotations

import json
from typing import Any

from backend.app.config import get_settings
from backend.app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        if not settings.allow_remote_llm:
            raise RuntimeError("ALLOW_REMOTE_LLM must be true before using OpenAIProvider.")
        from openai import OpenAI  # type: ignore

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4.1-mini"

    def complete_json(self, *, system: str, prompt: str, schema_hint: str) -> dict[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"{prompt}\n\nReturn JSON only matching this schema:\n{schema_hint}",
                },
            ],
            temperature=0,
        )
        text = response.output_text
        return json.loads(text)

    def generate_text(self, *, system: str, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.output_text
