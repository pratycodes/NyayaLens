from __future__ import annotations

from backend.app.core.schemas import ExpertRoute, IssueAnalysis


def route_expert(issue: IssueAnalysis) -> ExpertRoute:
    if issue.unsafe_request or issue.issue_type.endswith("_redirect_only"):
        return ExpertRoute(
            primary_expert="LegalAidSafetyExpert",
            secondary_experts=["VerifierExpert"],
            confidence="high",
            route_reason="Request needs safety handling and legal-aid oriented guidance.",
        )
    if issue.domain == "employment":
        secondary = ["ContractClauseExpert", "VerifierExpert"]
        return ExpertRoute(
            primary_expert="EmploymentExitExpert",
            secondary_experts=secondary,
            confidence=issue.confidence,
            route_reason=f"Employment issue detected: {issue.issue_type}.",
        )
    if issue.domain == "tenancy":
        return ExpertRoute(
            primary_expert="TenancyExpert",
            secondary_experts=["ContractClauseExpert", "LegalAidSafetyExpert", "VerifierExpert"],
            confidence=issue.confidence,
            route_reason=f"Tenancy issue detected: {issue.issue_type}.",
        )
    return ExpertRoute(
        primary_expert="ContractClauseExpert",
        secondary_experts=["LegalAidSafetyExpert", "VerifierExpert"],
        confidence="low",
        route_reason="Domain is uncertain, so the generic contract expert is primary.",
    )
