from __future__ import annotations

UNPAID_PAYMENT_ISSUES = {"unpaid_salary", "full_and_final", "unpaid_compensation", "payment_withheld"}

RESUME_INDICATORS = {
    "resume",
    "curriculum vitae",
    "education",
    "skills",
    "projects",
    "experience",
    "github",
    "linkedin",
}

PAYMENT_CONTRACT_INDICATORS = {
    "agreement",
    "employer",
    "employee",
    "contractor",
    "payment",
    "salary",
    "invoice",
    "consideration",
    "notice period",
    "termination",
    "jurisdiction",
    "offer letter",
    "appointment letter",
    "payslip",
    "full-and-final",
    "full and final",
    "bank statement",
    "attendance",
}

UNRELATED_PAYMENT_DOCUMENT_WARNING = (
    "The uploaded document does not appear to be payment-related or contract-related. "
    "Analysis is based mainly on the plain-text dispute description and user context."
)


def payment_document_relevance_warning(text: str, issue_type: str) -> str | None:
    if issue_type not in UNPAID_PAYMENT_ISSUES:
        return None
    lowered = text.lower()
    resume_hits = sum(1 for indicator in RESUME_INDICATORS if indicator in lowered)
    contract_hits = sum(1 for indicator in PAYMENT_CONTRACT_INDICATORS if indicator in lowered)
    if resume_hits >= 2 and contract_hits == 0:
        return UNRELATED_PAYMENT_DOCUMENT_WARNING
    return None
