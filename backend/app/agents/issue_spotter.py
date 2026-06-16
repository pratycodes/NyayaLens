from __future__ import annotations

from backend.app.agents.safety_guardrails import SAFE_REFUSAL, detect_unsafe_request
from backend.app.config import get_settings
from backend.app.core.schemas import DocumentAnalysis, IssueAnalysis, UserContext
from backend.app.llm.factory import get_llm_provider

EMPLOYMENT_KEYWORDS = {
    "bond_recovery": ["bond", "training cost", "recovery", "liquidated"],
    "non_compete": ["non-compete", "non compete", "competitor"],
    "notice_period": ["notice period", "resign", "resignation", "90 days", "60 days"],
    "unpaid_salary": ["salary withheld", "unpaid salary", "wages", "withhold salary"],
    "full_and_final": ["full and final", "fnf", "final settlement"],
    "relieving_letter": ["relieving", "experience letter", "service certificate"],
    "workplace_harassment_redirect_only": ["harassment", "hostile", "abuse at work"],
}

TENANCY_KEYWORDS = {
    "deposit_deduction": ["security deposit", "deposit", "deduct", "deduction"],
    "eviction_notice": ["eviction", "evict", "vacate", "lockout", "notice"],
    "rent_increase": ["rent increase", "rent hike", "increase rent"],
    "repair_dispute": ["repair", "maintenance", "damage", "leakage"],
    "lock_in_dispute": ["lock-in", "lock in", "lockin"],
    "landlord_harassment_redirect_only": ["harassment", "threaten", "landlord abuse"],
}


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


def _llm_issue_spotter(text: str, document: DocumentAnalysis, context: UserContext) -> IssueAnalysis | None:
    settings = get_settings()
    if settings.llm_provider.lower() == "mock" or not settings.allow_remote_llm:
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


def spot_issue(text: str, document: DocumentAnalysis, context: UserContext) -> IssueAnalysis:
    unsafe, matches = detect_unsafe_request(" ".join([text, context.query or ""]))
    if unsafe:
        return IssueAnalysis(
            domain=document.detected_domain if document.detected_domain != "unknown" else "unknown",
            issue_type="unsafe_request",
            confidence="high",
            reasons=[f"Unsafe request terms detected: {', '.join(matches)}"],
            unsafe_request=True,
            refusal_message=SAFE_REFUSAL,
        )

    llm_issue = _llm_issue_spotter(text, document, context)
    if llm_issue is not None:
        return llm_issue

    selected = (context.selected_dispute_type or "auto-detect").strip()
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

    if selected != "auto-detect":
        if selected in EMPLOYMENT_KEYWORDS:
            return IssueAnalysis(
                domain="employment",
                issue_type=selected,
                confidence="high",
                reasons=["User selected dispute type."],
            )
        if selected in TENANCY_KEYWORDS:
            return IssueAnalysis(
                domain="tenancy",
                issue_type=selected,
                confidence="high",
                reasons=["User selected dispute type."],
            )

    query_text = context.query or ""
    if query_text.strip():
        query_emp_issue, query_emp_score, query_emp_reasons = _score_keywords(
            query_text, EMPLOYMENT_KEYWORDS
        )
        query_ten_issue, query_ten_score, query_ten_reasons = _score_keywords(
            query_text, TENANCY_KEYWORDS
        )
        if query_emp_score > query_ten_score and query_emp_score > 0:
            return IssueAnalysis(
                domain="employment",
                issue_type=query_emp_issue,
                confidence="high" if query_emp_score >= 2 else "medium",
                reasons=query_emp_reasons,
            )
        if query_ten_score > query_emp_score and query_ten_score > 0:
            return IssueAnalysis(
                domain="tenancy",
                issue_type=query_ten_issue,
                confidence="high" if query_ten_score >= 2 else "medium",
                reasons=query_ten_reasons,
            )

    if document.detected_domain == "employment" or emp_score > ten_score:
        issue = emp_issue if emp_score else "employment_exit"
        return IssueAnalysis(
            domain="employment",
            issue_type=issue,
            confidence="high" if emp_score >= 2 else "medium",
            reasons=emp_reasons or ["Employment document detected."],
        )
    if document.detected_domain == "tenancy" or ten_score > emp_score:
        issue = ten_issue if ten_score else "deposit_deduction"
        return IssueAnalysis(
            domain="tenancy",
            issue_type=issue,
            confidence="high" if ten_score >= 2 else "medium",
            reasons=ten_reasons or ["Tenancy document detected."],
        )
    return IssueAnalysis(
        domain="unknown",
        issue_type="unknown",
        confidence="low",
        reasons=["Could not confidently classify the dispute."],
    )
