from __future__ import annotations

import re

from backend.app.core.schemas import SafetyResult

SAFE_REFUSAL = (
    "I cannot help with threats, forged evidence, impersonation, harassment, illegal lock-breaking, "
    "or other unlawful pressure tactics. A safer path is to preserve evidence, communicate in writing, "
    "ask for itemized reasons, and consult legal aid or a qualified lawyer for high-risk steps."
)

UNSAFE_INTENT_PATTERNS: list[tuple[str, str, str]] = [
    ("how_do_i_harass", r"\bhow\s+(?:do|can)\s+i\s+harass\b", "harass"),
    ("help_me_harass", r"\bhelp\s+me\s+harass\b", "harass"),
    ("how_do_i_threaten", r"\bhow\s+(?:do|can)\s+i\s+threaten\b", "threaten"),
    ("write_threat", r"\bwrite\s+(?:a\s+)?threat\b", "threat"),
    ("blackmail", r"\bblackmail\b", "blackmail"),
    ("forge", r"\bforge\b", "forge"),
    ("fake_document", r"\bfake\s+(?:document|notice|evidence)\b", "fake document"),
    ("impersonate", r"\bimpersonate\b", "impersonate"),
    ("break_lock", r"\bbreak\s+(?:the\s+)?lock\b", "break lock"),
    ("force_them", r"\bforce\s+them\b", "force them"),
    ("scare_them", r"\bscare\s+them\b", "scare them"),
    (
        "publish_private_information",
        r"\bpublish\s+(?:their\s+)?private\s+information\b",
        "publish private information",
    ),
    ("leak_data", r"\bleak\s+(?:their\s+)?data\b", "leak their data"),
    ("create_fake_evidence", r"\bcreate\s+fake\s+evidence\b", "create fake evidence"),
    ("destroy_evidence", r"\bdestroy\s+evidence\b", "destroy evidence"),
]


def detect_unsafe_request(text: str) -> SafetyResult:
    """Inspect only active user intent, never uploaded/corpus/generated text."""
    lowered = text.lower()
    matched_terms: list[str] = []
    matched_patterns: list[str] = []
    for name, pattern, term in UNSAFE_INTENT_PATTERNS:
        if re.search(pattern, lowered):
            matched_patterns.append(name)
            matched_terms.append(term)
    if matched_patterns:
        return SafetyResult(
            is_unsafe_intent=True,
            matched_terms=sorted(set(matched_terms)),
            matched_patterns=matched_patterns,
            scope="user_intent_only",
            reason="User intent asks for unlawful pressure, fabrication, impersonation, or harassment.",
        )
    return SafetyResult(
        is_unsafe_intent=False,
        matched_terms=[],
        matched_patterns=[],
        scope="user_intent_only",
        reason="No unsafe user intent detected in active user text.",
    )
