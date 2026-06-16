from __future__ import annotations

from backend.app.core.schemas import (
    Citation,
    DocumentAnalysis,
    IssueAnalysis,
    JurisdictionResult,
    RiskFlag,
    RuleResult,
    UserContext,
)
from backend.app.rules.employment_rules import evaluate_employment_rules
from backend.app.rules.risk_scoring import rules_to_risks
from backend.app.rules.tenancy_rules import evaluate_tenancy_rules

GENERAL_INFORMATION_PREFIX = "General information from deterministic checks:"


def _label_general_information(rules: list[RuleResult]) -> list[RuleResult]:
    for rule in rules:
        if not rule.explanation.startswith(GENERAL_INFORMATION_PREFIX):
            rule.explanation = f"{GENERAL_INFORMATION_PREFIX} {rule.explanation}"
    return rules


def apply_rules(
    *,
    document: DocumentAnalysis,
    issue: IssueAnalysis,
    context: UserContext,
    jurisdiction: JurisdictionResult,
    source_citations: list[Citation],
) -> tuple[list[RuleResult], list[RiskFlag]]:
    if issue.unsafe_request:
        rule = RuleResult(
            id="unsafe_request_refusal",
            passed=False,
            title="Unsafe request refused",
            severity="high",
            confidence="high",
            evidence=issue.reasons,
            explanation=issue.refusal_message or "Unsafe request detected.",
            suggested_next_step="Use lawful written communication and consult legal aid for high-risk situations.",
        )
        rules = _label_general_information([rule])
        return rules, rules_to_risks(rules, source_citations=source_citations)

    if issue.domain in {"employment", "contract_payment"}:
        rules = evaluate_employment_rules(document, context, jurisdiction, issue.issue_type)
    elif issue.domain == "tenancy":
        rules = evaluate_tenancy_rules(document, context, jurisdiction, issue.issue_type)
    else:
        rules = [
            RuleResult(
                id="unknown_domain_missing_context",
                passed=False,
                title="Dispute domain is unclear",
                severity="medium",
                confidence="high",
                evidence=[],
                explanation="The system could not confidently classify this as employment or tenancy.",
                suggested_next_step="Provide the document type, user role, counterparty, city/state, and dispute summary.",
            )
        ]
    rules = _label_general_information(rules)
    return rules, rules_to_risks(rules, source_citations=source_citations)
