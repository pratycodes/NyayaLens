from __future__ import annotations

from backend.app.core.schemas import Citation, Confidence, RiskFlag, RuleResult, Severity

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}


def overall_confidence(confidences: list[Confidence]) -> Confidence:
    if not confidences:
        return "low"
    if "low" in confidences:
        return "medium" if confidences.count("high") >= 2 else "low"
    if "medium" in confidences:
        return "medium"
    return "high"


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in value.split() if len(token) >= 5}


def _relevant_citations(rule: RuleResult, citations: list[Citation]) -> list[Citation]:
    rule_tokens = _tokens(" ".join([rule.title, rule.explanation, " ".join(rule.evidence)]))
    if not rule_tokens:
        return []
    relevant: list[Citation] = []
    for citation in citations:
        source_tokens = _tokens(" ".join([citation.title or "", citation.excerpt]))
        if len(rule_tokens.intersection(source_tokens)) >= 2:
            relevant.append(citation)
    return relevant[:2]


def rules_to_risks(
    rules: list[RuleResult],
    *,
    source_citations: list[Citation],
    document_citations_by_rule: dict[str, list[str]] | None = None,
) -> list[RiskFlag]:
    risks: list[RiskFlag] = []
    document_citations_by_rule = document_citations_by_rule or {}
    for rule in rules:
        if rule.passed:
            continue
        risks.append(
            RiskFlag(
                id=rule.id,
                title=rule.title,
                severity=rule.severity,
                confidence=rule.confidence,
                triggering_evidence=rule.evidence,
                explanation=rule.explanation,
                suggested_next_step=rule.suggested_next_step or "Collect more facts and get written clarification.",
                source_citations=_relevant_citations(rule, source_citations),
                document_citations=document_citations_by_rule.get(rule.id, rule.evidence[:2]),
            )
        )
    return sorted(risks, key=lambda risk: SEVERITY_RANK[risk.severity], reverse=True)


def max_severity(risks: list[RiskFlag]) -> Severity:
    if not risks:
        return "low"
    return max((risk.severity for risk in risks), key=lambda sev: SEVERITY_RANK[sev])  # type: ignore[return-value]
