from __future__ import annotations

from backend.app.config import get_settings
from backend.app.llm.base import LLMProvider
from backend.app.llm.mock_provider import MockLLMProvider
from backend.app.llm.openai_provider import OpenAIProvider


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider.lower() == "openai" and settings.allow_remote_llm:
        return OpenAIProvider()
    return MockLLMProvider()
