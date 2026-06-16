from __future__ import annotations

from typing import Any

from backend.app.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    def complete_json(self, *, system: str, prompt: str, schema_hint: str) -> dict[str, Any]:
        lowered = prompt.lower()
        if any(word in lowered for word in ["rent", "tenant", "landlord", "deposit"]):
            return {
                "domain": "tenancy",
                "issue_type": "deposit_deduction" if "deposit" in lowered else "eviction_notice",
                "confidence": "medium",
                "reasons": ["Mock provider matched tenancy keywords."],
            }
        return {
            "domain": "employment",
            "issue_type": "employment_exit",
            "confidence": "medium",
            "reasons": ["Mock provider matched employment-style request."],
        }

    def generate_text(self, *, system: str, prompt: str) -> str:
        return "Mock mode generated a conservative, template-based response."
