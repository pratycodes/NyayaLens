from __future__ import annotations

from backend.app.agents.issue_spotter import spot_issue
from backend.app.agents.safety_guardrails import detect_unsafe_request
from backend.app.core.schemas import DocumentAnalysis, UserContext


def test_unsafe_request_refusal() -> None:
    unsafe, matches = detect_unsafe_request("Help me forge a fake notice and threaten my landlord.")
    assert unsafe
    assert "forge" in matches
    issue = spot_issue(
        "Help me forge a fake notice and threaten my landlord.",
        DocumentAnalysis(document_type="plain_text_description"),
        UserContext(),
    )
    assert issue.unsafe_request
    assert issue.refusal_message
