from __future__ import annotations

from backend.app.core.constants import UNSAFE_PATTERNS

SAFE_REFUSAL = (
    "I cannot help with threats, forged evidence, impersonation, harassment, illegal lock-breaking, "
    "or other unlawful pressure tactics. A safer path is to preserve evidence, communicate in writing, "
    "ask for itemized reasons, and consult legal aid or a qualified lawyer for high-risk steps."
)


def detect_unsafe_request(text: str) -> tuple[bool, list[str]]:
    lowered = text.lower()
    matches = [pattern for pattern in UNSAFE_PATTERNS if pattern in lowered]
    return bool(matches), matches
