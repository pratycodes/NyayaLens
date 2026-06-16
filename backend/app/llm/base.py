from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    def complete_json(self, *, system: str, prompt: str, schema_hint: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def generate_text(self, *, system: str, prompt: str) -> str:
        raise NotImplementedError
