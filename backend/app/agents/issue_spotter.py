from __future__ import annotations

from backend.app.agents.issue_domain_consistency import validate_issue_domain
from backend.app.agents.safety_guardrails import SAFE_REFUSAL, detect_unsafe_request
from backend.app.config import get_settings
from backend.app.core.schemas import DocumentAnalysis, IssueAnalysis, UserContext
from backend.app.llm.factory import get_llm_provider

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

EMPLOYMENT_KEYWORDS = {
    "bond_recovery": ["bond", "training cost", "recovery", "liquidated"],
    "non_compete": ["non-compete", "non compete", "competitor"],
    "notice_period": ["notice period", "resign", "resignation", "90 days", "60 days"],
    "unpaid_salary": [
        "salary withheld",
        "unpaid salary",
        "wages",
        "withhold salary",
        "not been paid",
        "not paid",
        "pending payment",
        "payment pending",
        "payment withheld",
        "unpaid",
    ],
    "unpaid_compensation": ["unpaid compensation", "consulting fee", "freelance fee"],
    "payment_withheld": ["payment withheld", "withheld payment", "payment hold"],
    "invoice_unpaid": ["invoice not paid", "unpaid invoice", "client has not paid"],
    "payment_deduction": [
        "tds will be deducted",
        "tax deducted",
        "payment deduction",
        "invoice deduction",
        "compensation deduction",
        "tds",
    ],
    "contract_payment_review": [
        "consideration",
        "invoice",
        "payment shall be made",
        "pro-rata compensation",
        "independent contractor",
    ],
    "full_and_final": ["full and final", "fnf", "final settlement"],
    "relieving_letter": ["relieving", "experience letter", "service certificate"],
    "workplace_harassment_redirect_only": ["harassment", "hostile", "abuse at work"],
}

TENANCY_KEYWORDS = {
    "deposit_deduction": [
        "security deposit",
        "refundable deposit",
        "deposit refund",
        "deposit deduction",
        "deposit deductions",
        "deducted deposit",
        "deducted my deposit",
        "deposit not returned",
        "deposit withheld",
        "damage to flat",
        "damage to property",
        "painting charges",
        "repair bill",
    ],
    "eviction_notice": [
        "eviction",
        "evict",
        "vacate",
        "lockout",
        "eviction notice",
        "notice to vacate",
    ],
    "rent_increase": ["rent increase", "rent hike", "increase rent"],
    "repair_dispute": ["repair bill", "property damage", "maintenance issue", "leakage"],
    "lock_in_dispute": ["lock-in", "lock in", "lockin"],
    "landlord_harassment_redirect_only": ["harassment", "threaten", "landlord abuse"],
}

CONTRACTOR_ROLES = {"contractor", "freelancer", "consultant", "service provider"}
TENANCY_FALSE_POSITIVE_ISSUES = {
    "deposit_deduction",
    "repair_dispute",
    "eviction_notice",
    "rent_increase",
}
STRONG_TENANCY_INDICATORS = {
    "security deposit",
    "refundable deposit",
    "deposit refund",
    "landlord",
    "tenant",
    "rent agreement",
    "lease agreement",
    "monthly rent",
    "rental premises",
    "move-in",
    "move-out",
    "damage to flat",
    "damage to property",
    "painting charges",
    "repair bill",
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


def domain_for_issue(issue_type: str) -> str:
    return ISSUE_DOMAIN_MAP.get(issue_type, "unknown")


def _is_contractor_like(context: UserContext) -> bool:
    role = (context.user_role or "").strip().lower()
    return role in CONTRACTOR_ROLES


def _issue_for_role(
    issue_type: str,
    context: UserContext,
    document: DocumentAnalysis | None = None,
) -> str:
    is_freelance_document = document is not None and document.document_type == "freelance_service_agreement"
    if (
        (_is_contractor_like(context) or is_freelance_document)
        and issue_type in {"unpaid_salary", "payment_withheld"}
    ):
        return "unpaid_compensation"
    return issue_type


def _score_keywords(text: str, mapping: dict[str, list[str]]) -> tuple[str, int, list[str]]:
    best_issue = "unknown"
    best_score = 0
    reasons: list[str] = []
    lowered = text.lower()
    for issue, keywords in mapping.items():
        hits = [keyword for keyword in keywords if keyword in lowered]
        if len(hits) > best_score:
            best_issue = issue
            best_score = len(hits)
            reasons = [f"Matched keywords: {', '.join(hits)}"]
    return best_issue, best_score, reasons


def _contains_any(text: str, terms: set[str] | list[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _has_strong_tenancy_context(text: str) -> bool:
    return _contains_any(text, STRONG_TENANCY_INDICATORS)


def _contract_payment_issue_for_text(text: str, context: UserContext) -> str:
    if _contains_any(text, UNPAID_PAYMENT_INTENT_TERMS):
        return "unpaid_compensation" if _is_contractor_like(context) else "unpaid_salary"
    if _contains_any(text, DEDUCTION_PAYMENT_TERMS) or _contains_any(text, CONTRACT_PAYMENT_REVIEW_TERMS):
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


def _guard_freelance_tenancy_false_positive(
    issue: IssueAnalysis,
    document: DocumentAnalysis,
    context: UserContext,
    text: str,
) -> IssueAnalysis:
    if (
        document.document_type != "freelance_service_agreement"
        or issue.issue_type not in TENANCY_FALSE_POSITIVE_ISSUES
        or _has_strong_tenancy_context(text)
    ):
        return issue

    corrected_issue = _contract_payment_issue_for_text(" ".join([context.query or "", text]), context)
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


def _llm_issue_spotter(text: str, document: DocumentAnalysis, context: UserContext) -> IssueAnalysis | None:
    settings = get_settings()
    if (
        settings.llm_provider.lower() == "mock"
        or not settings.allow_remote_llm
        or not context.allow_remote_llm
    ):
        return None
    snippet = text[:4000]
    prompt = (
        "Classify this Indian employment-exit or tenancy dispute. "
        "Return only domain, issue_type, confidence, and reasons. "
        f"Document domain guess: {document.detected_domain}. "
        f"User context: {context.model_dump() if hasattr(context, 'model_dump') else context.dict()}.\n\n"
        f"Document excerpt:\n{snippet}"
    )
    try:
        data = get_llm_provider().complete_json(
            system="You classify disputes conservatively and never invent legal claims.",
            prompt=prompt,
            schema_hint=(
                "{domain: employment|tenancy|unknown, issue_type: string, "
                "confidence: low|medium|high, reasons: string[]}"
            ),
        )
        return IssueAnalysis(**data)
    except Exception:
        return None


def _normalized_selected_dispute(context: UserContext) -> str:
    selected = (context.selected_dispute_type or "auto-detect").strip()
    return "auto-detect" if selected in {"auto", "auto_detect", "auto-detect", ""} else selected


def _validated_auto_issue(
    issue: IssueAnalysis,
    *,
    text: str,
    document: DocumentAnalysis,
    context: UserContext,
) -> IssueAnalysis:
    return validate_issue_domain(
        issue,
        document=document,
        context=context,
        user_text=context.query or "",
        document_text=text,
    )


def spot_issue(
    text: str,
    document: DocumentAnalysis,
    context: UserContext,
    active_intent_text: str | None = None,
) -> IssueAnalysis:
    user_intent = active_intent_text if active_intent_text is not None else (context.query or "")
    safety = detect_unsafe_request(user_intent)
    if safety.is_unsafe_intent:
        return IssueAnalysis(
            domain="safety",
            issue_type="unsafe_request",
            confidence="high",
            reasons=[f"Unsafe user-intent patterns detected: {', '.join(safety.matched_patterns)}"],
            unsafe_request=True,
            refusal_message=SAFE_REFUSAL,
            safety_result=safety,
        )

    selected = _normalized_selected_dispute(context)
    if selected != "auto-detect":
        selected_domain = domain_for_issue(selected)
        if selected_domain != "unknown":
            return IssueAnalysis(
                domain=selected_domain,  # type: ignore[arg-type]
                issue_type=selected,
                confidence="high",
                reasons=["User selected dispute type."],
                safety_result=safety,
            )

    llm_issue = _llm_issue_spotter(text, document, context)
    if llm_issue is not None:
        llm_issue.safety_result = safety
        return _validated_auto_issue(llm_issue, text=text, document=document, context=context)

    combined = " ".join(
        [
            text,
            context.query or "",
            " ".join(clause.name for clause in document.extracted_clauses),
            " ".join(clause.raw_text for clause in document.extracted_clauses),
        ]
    )
    emp_issue, emp_score, emp_reasons = _score_keywords(combined, EMPLOYMENT_KEYWORDS)
    ten_issue, ten_score, ten_reasons = _score_keywords(combined, TENANCY_KEYWORDS)

    query_text = context.query or ""
    if query_text.strip():
        query_emp_issue, query_emp_score, query_emp_reasons = _score_keywords(
            query_text, EMPLOYMENT_KEYWORDS
        )
        query_ten_issue, query_ten_score, query_ten_reasons = _score_keywords(
            query_text, TENANCY_KEYWORDS
        )
        if query_emp_score > query_ten_score and query_emp_score > 0:
            issue_type = _issue_for_role(query_emp_issue, context, document)
            return _validated_auto_issue(IssueAnalysis(
                domain=domain_for_issue(issue_type),  # type: ignore[arg-type]
                issue_type=issue_type,
                confidence="high" if query_emp_score >= 2 else "medium",
                reasons=query_emp_reasons,
                safety_result=safety,
            ), text=text, document=document, context=context)
        if query_ten_score > query_emp_score and query_ten_score > 0:
            issue = IssueAnalysis(
                domain="tenancy",
                issue_type=query_ten_issue,
                confidence="high" if query_ten_score >= 2 else "medium",
                reasons=query_ten_reasons,
                safety_result=safety,
            )
            return _validated_auto_issue(issue, text=text, document=document, context=context)

    if document.detected_domain == "contract_payment" or document.document_type == "freelance_service_agreement":
        issue = _contract_payment_issue_for_text(combined, context)
        return _validated_auto_issue(IssueAnalysis(
            domain=domain_for_issue(issue),  # type: ignore[arg-type]
            issue_type=issue,
            confidence="medium",
            reasons=[_contract_payment_reason(issue, document)],
            safety_result=safety,
        ), text=text, document=document, context=context)

    if document.detected_domain == "employment" or emp_score > ten_score:
        issue = _issue_for_role(emp_issue, context, document) if emp_score else "employment_exit"
        return _validated_auto_issue(IssueAnalysis(
            domain=domain_for_issue(issue),  # type: ignore[arg-type]
            issue_type=issue,
            confidence="high" if emp_score >= 2 else "medium",
            reasons=emp_reasons or ["Employment document detected."],
            safety_result=safety,
        ), text=text, document=document, context=context)
    if document.detected_domain == "tenancy" or ten_score > emp_score:
        issue = ten_issue if ten_score else "deposit_deduction"
        issue_analysis = IssueAnalysis(
            domain="tenancy",
            issue_type=issue,
            confidence="high" if ten_score >= 2 else "medium",
            reasons=ten_reasons or ["Tenancy document detected."],
            safety_result=safety,
        )
        return _validated_auto_issue(issue_analysis, text=text, document=document, context=context)
    return IssueAnalysis(
        domain="unknown",
        issue_type="unknown",
        confidence="low",
        reasons=["Could not confidently classify the dispute."],
        safety_result=safety,
    )
