from __future__ import annotations

import re

from backend.app.core.schemas import (
    Citation,
    IssueAnalysis,
    JurisdictionResult,
    RemedyPlan,
    RiskFlag,
    RuleResult,
    VerifierResult,
)

SECTION_RE = re.compile(r"\b(?:section|sec\.)\s+\d+[a-zA-Z-]*\b", re.IGNORECASE)
GUARANTEE_RE = re.compile(r"\b(?:will win|guaranteed|definitely illegal|must be invalid|assured outcome)\b", re.IGNORECASE)


def verify_report_parts(
    *,
    disclaimer: str,
    issue: IssueAnalysis,
    jurisdiction: JurisdictionResult,
    rules: list[RuleResult],
    risks: list[RiskFlag],
    remedy: RemedyPlan,
    citations: list[Citation],
) -> VerifierResult:
    warnings: list[str] = []
    joined_output = " ".join(
        [
            disclaimer,
            " ".join(rule.explanation for rule in rules),
            " ".join(risk.explanation for risk in risks),
            " ".join(remedy.steps),
            remedy.draft_message or "",
        ]
    )
    source_text = " ".join(citation.excerpt for citation in citations)

    if "legal information" not in disclaimer.lower() or "not legal advice" not in disclaimer.lower():
        warnings.append("Legal information disclaimer is missing or incomplete.")
    for match in SECTION_RE.findall(joined_output):
        if match.lower() not in source_text.lower():
            warnings.append(f"Exact legal section appears without retrieved citation support: {match}.")
    if jurisdiction.confidence == "high" and not jurisdiction.state:
        warnings.append("Jurisdiction confidence is overclaimed.")
    if GUARANTEE_RE.search(joined_output):
        warnings.append("Outcome appears guaranteed or overclaimed.")
    if issue.unsafe_request and not any(rule.id == "unsafe_request_refusal" for rule in rules):
        warnings.append("Unsafe request was not refused by rules.")
    if risks and not citations:
        warnings.append("Risk report has no retrieved source citations.")

    passed = not warnings
    return VerifierResult(
        passed=passed,
        warnings=warnings,
        conservative_message=None
        if passed
        else "Not enough verified source material was found to answer confidently.",
    )
