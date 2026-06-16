from __future__ import annotations

from backend.app.core.schemas import DocumentAnalysis, IssueAnalysis, UserContext

ISSUE_DOMAIN_MAP = {
    "unpaid_salary": "employment",
    "unpaid_compensation": "contract_payment",
    "payment_withheld": "contract_payment",
    "invoice_unpaid": "contract_payment",
    "payment_deduction": "contract_payment",
    "contract_payment_review": "contract_payment",
    "freelance_agreement_review": "contract_payment",
    "full_and_final": "employment",
    "bond_recovery": "employment",
    "notice_period": "employment",
    "non_compete": "employment",
    "employment_exit": "employment",
    "relieving_letter": "employment",
    "workplace_harassment_redirect_only": "employment",
    "deposit_deduction": "tenancy",
    "eviction_notice": "tenancy",
    "rent_increase": "tenancy",
    "repair_dispute": "tenancy",
    "lock_in_dispute": "tenancy",
    "landlord_harassment_redirect_only": "tenancy",
    "unsafe_request": "safety",
}

CONTRACTOR_ROLES = {"contractor", "freelancer", "consultant", "service provider"}
TENANCY_FALSE_POSITIVE_ISSUES = {
    "deposit_deduction",
    "repair_dispute",
    "eviction_notice",
    "rent_increase",
    "lock_in_dispute",
}
STRONG_TENANCY_INDICATORS = {
    "tenant",
    "landlord",
    "rent agreement",
    "lease agreement",
    "monthly rent",
    "security deposit",
    "refundable deposit",
    "deposit refund",
    "eviction",
    "move-in",
    "move-out",
    "painting charges",
    "repair bill",
    "rental premises",
    "lessor",
    "lessee",
}
UNPAID_PAYMENT_INTENT_TERMS = {
    "unpaid salary",
    "unpaid compensation",
    "not paid",
    "not been paid",
    "payment pending",
    "pending payment",
    "invoice unpaid",
    "invoice not paid",
    "client has not paid",
    "company has not paid",
    "salary/fnf pending",
    "fnf pending",
}
DEDUCTION_PAYMENT_TERMS = {
    "tds will be deducted",
    "tax deducted",
    "payment deduction",
    "invoice deduction",
    "compensation deduction",
    "tds",
}
CONTRACT_PAYMENT_REVIEW_TERMS = {
    "consideration",
    "invoice",
    "payment shall be made",
    "pro-rata compensation",
    "independent contractor",
}
CONTRACT_REMEDY_TERMS = {
    "monetary damages would not be adequate",
    "injunctive relief",
    "irreparable harm",
    "breach of agreement",
}


def domain_for_issue(issue_type: str) -> str:
    return ISSUE_DOMAIN_MAP.get(issue_type, "unknown")


def is_contractor_like(context: UserContext) -> bool:
    return (context.user_role or "").strip().lower() in CONTRACTOR_ROLES


def contains_any(text: str, terms: set[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def has_strong_tenancy_context(text: str) -> bool:
    return contains_any(text, STRONG_TENANCY_INDICATORS)


def has_unpaid_payment_intent(text: str) -> bool:
    return contains_any(text, UNPAID_PAYMENT_INTENT_TERMS)


def contract_payment_issue_for_text(text: str, context: UserContext) -> str:
    if has_unpaid_payment_intent(text):
        return "unpaid_compensation" if is_contractor_like(context) else "unpaid_salary"
    if contains_any(text, DEDUCTION_PAYMENT_TERMS | CONTRACT_PAYMENT_REVIEW_TERMS):
        return "contract_payment_review"
    return "contract_payment_review"


def _contract_payment_reason(issue_type: str, document: DocumentAnalysis) -> str:
    if issue_type == "unpaid_compensation":
        return "Payment-related user intent and contractor/service-provider context detected."
    if issue_type == "unpaid_salary":
        return "Payment-related user intent detected."
    if issue_type == "contract_payment_review":
        return "Freelance/service agreement payment or deduction terms detected."
    if document.document_type == "freelance_service_agreement":
        return "Freelance/service agreement detected."
    return "Contract payment context detected."


def validate_issue_domain(
    issue: IssueAnalysis,
    *,
    document: DocumentAnalysis,
    context: UserContext,
    user_text: str,
    document_text: str,
) -> IssueAnalysis:
    """Correct issue/domain pairs that conflict with strong document context.

    Safety blocking is intentionally excluded here; unsafe intent detection happens
    before this function and only receives user-intent text.
    """
    if issue.unsafe_request:
        return issue

    combined = " ".join([user_text, document_text])
    if (
        document.document_type == "freelance_service_agreement"
        and has_unpaid_payment_intent(user_text)
    ):
        return IssueAnalysis(
            domain="contract_payment",
            issue_type="unpaid_compensation",
            confidence="high" if issue.confidence == "high" else "medium",
            reasons=[
                "Unpaid payment issue for a contractor/freelancer based on a service agreement.",
                *issue.reasons,
            ],
            safety_result=issue.safety_result,
        )

    if (
        document.document_type == "freelance_service_agreement"
        and issue.issue_type in TENANCY_FALSE_POSITIVE_ISSUES
        and not has_strong_tenancy_context(combined)
    ):
        corrected_issue = contract_payment_issue_for_text(combined, context)
        warning = (
            "Tenancy issue was not selected because the uploaded document appears to be a "
            "freelance/service agreement and no strong tenancy indicators were found."
        )
        return IssueAnalysis(
            domain=domain_for_issue(corrected_issue),  # type: ignore[arg-type]
            issue_type=corrected_issue,
            confidence="medium",
            reasons=[warning, _contract_payment_reason(corrected_issue, document)],
            safety_result=issue.safety_result,
        )

    if (
        issue.issue_type == "deposit_deduction"
        and not has_strong_tenancy_context(combined)
        and contains_any(combined, DEDUCTION_PAYMENT_TERMS)
    ):
        return IssueAnalysis(
            domain="contract_payment",
            issue_type="contract_payment_review",
            confidence="medium",
            reasons=[
                "Deduction wording appears payment/tax-related, not a tenancy security-deposit dispute.",
                *issue.reasons,
            ],
            safety_result=issue.safety_result,
        )

    if issue.issue_type == "repair_dispute" and contains_any(combined, CONTRACT_REMEDY_TERMS):
        return IssueAnalysis(
            domain="contract_payment" if document.document_type == "freelance_service_agreement" else issue.domain,
            issue_type=(
                "contract_payment_review"
                if document.document_type == "freelance_service_agreement"
                else issue.issue_type
            ),
            confidence="medium",
            reasons=[
                "Generic contract remedy language was not treated as a tenancy repair dispute.",
                *issue.reasons,
            ],
            safety_result=issue.safety_result,
        )

    if issue.domain == "unknown":
        mapped_domain = domain_for_issue(issue.issue_type)
        if mapped_domain != "unknown":
            issue.domain = mapped_domain  # type: ignore[assignment]
    return issue
