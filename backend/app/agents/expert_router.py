from __future__ import annotations

from backend.app.core.schemas import DocumentAnalysis, ExpertRoute, IssueAnalysis, UserContext

UNPAID_PAYMENT_ISSUES = {"unpaid_salary", "unpaid_compensation", "payment_withheld", "invoice_unpaid"}
CONTRACT_REVIEW_ISSUES = {
    "contract_payment_review",
    "freelance_agreement_review",
    "payment_deduction",
}


def route_expert(
    issue: IssueAnalysis,
    context: UserContext | None = None,
    document: DocumentAnalysis | None = None,
) -> ExpertRoute:
    if issue.unsafe_request or issue.issue_type.endswith("_redirect_only"):
        return ExpertRoute(
            primary_expert="LegalAidSafetyExpert",
            secondary_experts=["VerifierExpert"],
            confidence="high",
            route_reason="Request needs safety handling and legal-aid oriented guidance.",
        )
    if issue.issue_type in UNPAID_PAYMENT_ISSUES:
        user_role = (context.user_role or "").strip().lower() if context else ""
        if user_role in {"contractor", "freelancer", "consultant", "service provider"} or (
            document and document.document_type == "freelance_service_agreement"
        ):
            reason = "Unpaid payment issue for a contractor/freelancer/service provider."
            if document and document.document_type == "freelance_service_agreement":
                reason = "Unpaid payment issue for a contractor/freelancer based on a service agreement."
            return ExpertRoute(
                primary_expert="UnpaidCompensationExpert",
                secondary_experts=["ContractClauseExpert", "VerifierExpert"],
                confidence=issue.confidence,
                route_reason=reason,
            )
        return ExpertRoute(
            primary_expert="EmploymentCompensationExpert",
            secondary_experts=["EmploymentExitExpert", "ContractClauseExpert", "VerifierExpert"],
            confidence=issue.confidence,
            route_reason="Employment compensation or wage-related issue detected.",
        )
    if (
        issue.issue_type in CONTRACT_REVIEW_ISSUES
        and document
        and document.document_type == "freelance_service_agreement"
    ):
        return ExpertRoute(
            primary_expert="ContractClauseExpert",
            secondary_experts=["UnpaidCompensationExpert", "VerifierExpert"],
            confidence=issue.confidence,
            route_reason="Freelance/service agreement detected; reviewing payment and dispute-resolution clauses.",
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
    if issue.domain == "contract_payment":
        return ExpertRoute(
            primary_expert="ContractClauseExpert",
            secondary_experts=["UnpaidCompensationExpert", "VerifierExpert"],
            confidence=issue.confidence,
            route_reason=f"Contract payment issue detected: {issue.issue_type}.",
        )
    return ExpertRoute(
        primary_expert="ContractClauseExpert",
        secondary_experts=["LegalAidSafetyExpert", "VerifierExpert"],
        confidence="low",
        route_reason="Domain is uncertain, so the generic contract expert is primary.",
    )
