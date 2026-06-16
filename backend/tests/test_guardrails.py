from __future__ import annotations

from backend.app.agents.issue_spotter import spot_issue
from backend.app.agents.safety_guardrails import detect_unsafe_request
from backend.app.core.schemas import DocumentAnalysis, UserContext


def test_unsafe_request_refusal() -> None:
    safety = detect_unsafe_request("Help me forge a fake notice and threaten my landlord.")
    assert safety.is_unsafe_intent
    assert "forge" in safety.matched_terms
    assert safety.scope == "user_intent_only"
    issue = spot_issue(
        "Help me forge a fake notice and threaten my landlord.",
        DocumentAnalysis(document_type="plain_text_description"),
        UserContext(),
        active_intent_text="Help me forge a fake notice and threaten my landlord.",
    )
    assert issue.unsafe_request
    assert issue.refusal_message
    assert issue.domain == "safety"
