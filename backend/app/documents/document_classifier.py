from __future__ import annotations

from backend.app.core.schemas import Confidence


def classify_document(text: str) -> tuple[str, str, Confidence]:
    lowered = text.lower()
    employment_hits = sum(
        word in lowered
        for word in [
            "employee",
            "employer",
            "salary",
            "notice period",
            "relieving",
            "full and final",
            "non-compete",
            "training bond",
        ]
    )
    tenancy_hits = sum(
        word in lowered
        for word in [
            "tenant",
            "landlord",
            "rent",
            "security deposit",
            "eviction",
            "lock-in",
            "premises",
        ]
    )
    if employment_hits > tenancy_hits and employment_hits >= 2:
        return "employment_document", "employment", "high" if employment_hits >= 4 else "medium"
    if tenancy_hits > employment_hits and tenancy_hits >= 2:
        return "tenancy_document", "tenancy", "high" if tenancy_hits >= 4 else "medium"
    if "agreement" in lowered or "contract" in lowered:
        return "contract_document", "unknown", "low"
    return "plain_text_description", "unknown", "low"
