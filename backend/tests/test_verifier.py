from __future__ import annotations

from backend.app.agents.verifier_agent import verify_report_parts
from backend.app.core.constants import LEGAL_DISCLAIMER
from backend.app.core.schemas import (
    Citation,
    IssueAnalysis,
    JurisdictionResult,
    RemedyPlan,
    RiskFlag,
    RuleResult,
)


def test_verifier_catches_uncited_legal_section() -> None:
    rule = RuleResult(
        id="bad_section",
        passed=False,
        title="Bad section",
        severity="high",
        confidence="high",
        explanation="Section 999 requires payment immediately.",
        suggested_next_step="Ask politely.",
    )
    result = verify_report_parts(
        disclaimer=LEGAL_DISCLAIMER,
        issue=IssueAnalysis(domain="employment", issue_type="employment_exit", confidence="medium"),
        jurisdiction=JurisdictionResult(state="Karnataka", city="Bengaluru", confidence="high"),
        rules=[rule],
        risks=[
            RiskFlag(
                id="bad_section",
                title="Bad section",
                severity="high",
                confidence="high",
                explanation="Section 999 requires payment immediately.",
                suggested_next_step="Ask politely.",
            )
        ],
        remedy=RemedyPlan(steps=["Ask for written details."]),
        citations=[
            Citation(
                source_file="demo.txt",
                title="Demo",
                excerpt="No exact sections here.",
            )
        ],
    )
    assert not result.passed
    assert any("Section 999" in warning for warning in result.warnings)
