from __future__ import annotations

from backend.app.core.schemas import ExtractedClause, FinalReport

UNPAID_PAYMENT_ISSUES = {
    "unpaid_salary",
    "unpaid_compensation",
    "payment_withheld",
    "invoice_unpaid",
    "full_and_final",
}

PAYMENT_PRIORITY_CLAUSES = [
    "consideration_clause",
    "invoice_clause",
    "payment_timing_clause",
    "compensation_clause",
    "pro_rata_compensation_clause",
    "tds_clause",
    "independent_contractor_clause",
    "termination_notice_clause",
    "arbitration_clause",
    "jurisdiction_clause",
]


def key_fact_clauses(report: FinalReport, *, limit: int = 10) -> list[ExtractedClause]:
    clauses = report.extracted_facts.extracted_clauses
    is_contract_payment = (
        report.extracted_facts.document_type == "freelance_service_agreement"
        and report.issue_detected.domain == "contract_payment"
    )
    if is_contract_payment or report.issue_detected.issue_type in UNPAID_PAYMENT_ISSUES:
        ordered: list[ExtractedClause] = []
        seen: set[str] = set()
        for name in PAYMENT_PRIORITY_CLAUSES:
            clause = next((item for item in clauses if item.name == name), None)
            if clause and clause.name not in seen:
                ordered.append(clause)
                seen.add(clause.name)
        return ordered[:limit]
    return clauses[:6]
