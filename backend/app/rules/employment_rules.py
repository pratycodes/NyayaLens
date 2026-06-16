from __future__ import annotations

import re

from backend.app.core.schemas import DocumentAnalysis, JurisdictionResult, RuleResult, UserContext

UNPAID_PAYMENT_ISSUES = {
    "unpaid_salary",
    "full_and_final",
    "unpaid_compensation",
    "payment_withheld",
    "invoice_unpaid",
}
CONTRACT_PAYMENT_REVIEW_ISSUES = {
    "contract_payment_review",
    "freelance_agreement_review",
    "payment_deduction",
}
PAYMENT_CONFIDENCE_TERMS = [
    "not been paid",
    "not paid",
    "unpaid",
    "withheld",
    "pending payment",
    "payment pending",
    "salary",
    "invoice",
    "full and final",
    "fnf",
]


def _clauses(document: DocumentAnalysis, name: str) -> list[str]:
    return [clause.raw_text for clause in document.extracted_clauses if clause.name == name]


def _notice_days(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(day|days|month|months)", text, flags=re.IGNORECASE)
    if not match:
        return None
    value = int(match.group(1))
    return value * 30 if match.group(2).lower().startswith("month") else value


def _has_payment_evidence(document: DocumentAnalysis) -> bool:
    payment_clause_names = {
        "salary_withholding",
        "full_and_final_settlement",
        "consideration_clause",
        "invoice_clause",
        "payment_timing_clause",
        "compensation_clause",
        "tds_clause",
        "bond_amount",
        "training_cost",
        "jurisdiction_clause",
        "arbitration_clause",
    }
    if document.amounts:
        return True
    return any(clause.name in payment_clause_names for clause in document.extracted_clauses)


def _evaluate_unpaid_payment_rules(
    document: DocumentAnalysis,
    context: UserContext,
    jurisdiction: JurisdictionResult,
    issue_type: str,
) -> list[RuleResult]:
    query = context.query or ""
    lowered_query = query.lower()
    confidence = "high" if any(term in lowered_query for term in PAYMENT_CONFIDENCE_TERMS) else "medium"
    evidence = [f"issue_type: {issue_type}"]
    if query.strip():
        evidence.append(f"plain_text_dispute_description: {query.strip()}")

    results = [
        RuleResult(
            id="employment_unpaid_compensation_issue",
            passed=False,
            title="Unpaid compensation/payment issue",
            severity="high",
            confidence=confidence,  # type: ignore[arg-type]
            evidence=evidence,
            explanation=(
                "General information from deterministic checks. Unpaid wages, exit settlement, or "
                "contractor payments should be documented in writing with proof of agreed amount, "
                "work performed, due date, and prior payment follow-ups."
            ),
            suggested_next_step=(
                "Preserve contract/offer letter/service agreement, payslips/invoices, bank statements, "
                "work proof, and written payment follow-ups."
            ),
        )
    ]

    evidence_gap = (
        "No contract, payslip, invoice, amount due, or payment-term evidence was detected."
        if not _has_payment_evidence(document)
        else "Payment terms were found, but the unpaid amount, invoice/payment request, work period, and payment follow-up evidence are still missing."
    )
    results.append(
        RuleResult(
            id="employment_missing_payment_evidence",
            passed=False,
            title="Missing payment evidence",
            severity="medium",
            confidence="high",
            evidence=[evidence_gap],
            explanation=(
                "The system could not identify complete documents showing unpaid amount, due date, "
                "invoice/payment request, proof of work delivered, and written payment follow-ups."
            ),
            suggested_next_step=(
                "Upload offer letter, contract/service agreement, payslip, invoice, attendance/work logs, "
                "work delivery proof, or payment emails."
            ),
        )
    )

    payment_evidence = [
        clause.raw_text
        for clause in document.extracted_clauses
        if clause.name
        in {
            "consideration_clause",
            "invoice_clause",
            "payment_timing_clause",
            "compensation_clause",
            "tds_clause",
        }
    ]
    if payment_evidence:
        results.append(
            RuleResult(
                id="employment_payment_clause_compare_amount",
                passed=False,
                title="Payment clause found; compare unpaid amount against agreement",
                severity="medium",
                confidence="high",
                evidence=payment_evidence[:4],
                explanation=(
                    "The uploaded document appears to contain payment, invoice, consideration, or "
                    "compensation terms that should be compared with the unpaid amount and work period."
                ),
                suggested_next_step=(
                    "Match the unpaid amount against the invoice/payment clause, compensation table, "
                    "work delivered, and due date."
                ),
            )
        )

    deduction_evidence = [
        clause.raw_text
        for clause in document.extracted_clauses
        if clause.name == "tds_clause"
        or any(term in clause.raw_text.lower() for term in ["tds", "tax deducted", "deduction"])
    ]
    if deduction_evidence:
        results.append(
            RuleResult(
                id="employment_payment_deduction_clarification",
                passed=False,
                title="TDS/deduction clarification needed",
                severity="medium",
                confidence="medium",
                evidence=deduction_evidence[:3],
                explanation=(
                    "General information from deterministic checks. Tax, TDS, adjustment, penalty, "
                    "or withholding wording should be separated from any disputed non-payment amount."
                ),
                suggested_next_step=(
                    "Ask for an itemized calculation showing whether the deduction is TDS, a contractual "
                    "adjustment, a penalty, or disputed withholding."
                ),
            )
        )

    if (context.user_role or "").strip().lower() in {
        "contractor",
        "freelancer",
        "consultant",
        "service provider",
    }:
        results.append(
            RuleResult(
                id="employment_contractor_classification_ambiguity",
                passed=False,
                title="Contractor/freelancer classification ambiguity",
                severity="medium",
                confidence="high",
                evidence=["user_role: contractor"],
                explanation=(
                    "Different routes may apply depending on whether the person is an employee, contractor, "
                    "intern, freelancer, or consultant."
                ),
                suggested_next_step=(
                    "Clarify whether payment is salary, stipend, full-and-final settlement, invoice amount, "
                    "consulting fee, or freelance fee."
                ),
            )
        )

    location = ", ".join(part for part in [context.city, context.state] if part) or "state/city missing"
    if jurisdiction.state:
        location = ", ".join(part for part in [jurisdiction.city, jurisdiction.state] if part)
    results.append(
        RuleResult(
            id="employment_jurisdiction_remedy_route",
            passed=False,
            title="Jurisdiction-specific remedy route needed",
            severity="medium",
            confidence="medium",
            evidence=[f"location: {location}"],
            explanation=(
                "Available routes may depend on state, worker category, contract terms, and whether the "
                "dispute is employment, labour, civil, or contract-related."
            ),
            suggested_next_step=(
                "Confirm workplace/service location, contract jurisdiction, and payment due date."
            ),
        )
    )

    arbitration_or_jurisdiction = [
        clause.raw_text
        for clause in document.extracted_clauses
        if clause.name in {"arbitration_clause", "jurisdiction_clause"}
    ]
    if arbitration_or_jurisdiction:
        results.append(
            RuleResult(
                id="employment_payment_dispute_forum_clause",
                passed=False,
                title="Arbitration/jurisdiction clause may affect dispute path",
                severity="medium",
                confidence="medium",
                evidence=arbitration_or_jurisdiction[:3],
                explanation=(
                    "Arbitration or jurisdiction wording may affect where or how a payment dispute is raised."
                ),
                suggested_next_step=(
                    "Preserve the forum clause and ask legal aid or a lawyer how it affects the next step."
                ),
            )
        )
    return results


def _evaluate_contract_payment_review_rules(document: DocumentAnalysis) -> list[RuleResult]:
    results: list[RuleResult] = []
    payment_terms = [
        clause.raw_text
        for clause in document.extracted_clauses
        if clause.name
        in {
            "consideration_clause",
            "compensation_clause",
            "pro_rata_compensation_clause",
        }
    ]
    if payment_terms:
        results.append(
            RuleResult(
                id="contract_payment_terms_found",
                passed=False,
                title="Payment terms found; unpaid status not specified",
                severity="low",
                confidence="high",
                evidence=payment_terms[:3],
                explanation=(
                    "The uploaded service agreement includes payment or compensation terms, but the "
                    "current unpaid amount, due date, and payment status are not specified."
                ),
                suggested_next_step=(
                    "Compare the payment terms with the actual unpaid month, invoice, work delivered, "
                    "and payment follow-up history."
                ),
            )
        )

    invoice_timing = [
        clause.raw_text
        for clause in document.extracted_clauses
        if clause.name in {"invoice_clause", "payment_timing_clause"}
    ]
    if invoice_timing:
        results.append(
            RuleResult(
                id="contract_invoice_payment_timing_review",
                passed=False,
                title="Invoice/payment timing clause should be matched against actual unpaid period",
                severity="medium",
                confidence="high",
                evidence=invoice_timing[:3],
                explanation=(
                    "Invoice generation and payment timing clauses can help identify the expected due "
                    "date, but they need to be matched with the actual work period and invoice records."
                ),
                suggested_next_step=(
                    "Identify the unpaid work period, invoice date, invoice approval status, and expected payment date."
                ),
            )
        )

    tds = _clauses(document, "tds_clause")
    if tds:
        results.append(
            RuleResult(
                id="contract_tds_deduction_review",
                passed=False,
                title="TDS/deduction clause may need clarification",
                severity="medium",
                confidence="medium",
                evidence=tds[:3],
                explanation=(
                    "TDS or deduction wording affects net payable amount and should be separated from "
                    "contractual adjustment, penalty, or disputed withholding."
                ),
                suggested_next_step=(
                    "Ask for an itemized calculation showing TDS, any adjustment, and the remaining payable amount."
                ),
            )
        )

    relationship = _clauses(document, "independent_contractor_clause")
    if relationship:
        results.append(
            RuleResult(
                id="contract_independent_contractor_route",
                passed=False,
                title="Independent contractor relationship may affect remedy route",
                severity="medium",
                confidence="high",
                evidence=relationship[:2],
                explanation=(
                    "An independent contractor relationship can affect whether the practical route is "
                    "contract, civil, labour, or legal-aid oriented."
                ),
                suggested_next_step=(
                    "Clarify whether the payment is salary, invoice amount, consulting fee, freelance fee, or another category."
                ),
            )
        )

    forum = [
        clause.raw_text
        for clause in document.extracted_clauses
        if clause.name in {"arbitration_clause", "jurisdiction_clause"}
    ]
    if forum:
        results.append(
            RuleResult(
                id="contract_payment_forum_clause",
                passed=False,
                title="Arbitration/jurisdiction clause may affect dispute path",
                severity="medium",
                confidence="medium",
                evidence=forum[:3],
                explanation=(
                    "Arbitration or jurisdiction wording may affect where or how a contract payment dispute is raised."
                ),
                suggested_next_step=(
                    "Preserve the forum clause and ask legal aid or a lawyer how it affects the next step."
                ),
            )
        )
    return results


def evaluate_employment_rules(
    document: DocumentAnalysis,
    context: UserContext,
    jurisdiction: JurisdictionResult,
    issue_type: str,
) -> list[RuleResult]:
    results: list[RuleResult] = []
    query = (context.query or "").lower()

    if issue_type in UNPAID_PAYMENT_ISSUES:
        results.extend(_evaluate_unpaid_payment_rules(document, context, jurisdiction, issue_type))
    elif issue_type in CONTRACT_PAYMENT_REVIEW_ISSUES:
        results.extend(_evaluate_contract_payment_review_rules(document))

    bond = _clauses(document, "bond_amount")
    if bond:
        results.append(
            RuleResult(
                id="employment_bond_recovery",
                passed=False,
                title="Employment bond or training recovery detected",
                severity="high",
                confidence="high",
                evidence=bond,
                explanation=(
                    "A bond/recovery clause can create a high practical risk. The amount should be checked "
                    "against the agreement, actual training cost proof, resignation timing, and role facts."
                ),
                suggested_next_step="Ask for the training agreement, itemized cost calculation, and proof of actual expense.",
            )
        )

    training = _clauses(document, "training_cost")
    if training and not bond:
        results.append(
            RuleResult(
                id="employment_training_cost",
                passed=False,
                title="Training cost recovery wording detected",
                severity="medium",
                confidence="medium",
                evidence=training,
                explanation="Training recovery depends on documents and proof of actual cost.",
                suggested_next_step="Request an itemized calculation and preserve all training-related documents.",
            )
        )

    non_compete = _clauses(document, "non_compete_duration")
    if non_compete:
        results.append(
            RuleResult(
                id="employment_non_compete_review",
                passed=False,
                title="Post-employment non-compete detected",
                severity="high",
                confidence="high",
                evidence=non_compete,
                explanation="Post-employment restrictions are high-risk and should not be treated as automatically valid or invalid.",
                suggested_next_step="Get legal review before joining a competitor or responding to a non-compete threat.",
            )
        )

    salary = _clauses(document, "salary_withholding") + _clauses(document, "full_and_final_settlement")
    if salary and any(word in query for word in ["withheld", "unpaid", "not paid", "salary", "fnf"]):
        results.append(
            RuleResult(
                id="employment_salary_withholding",
                passed=False,
                title="Salary or final settlement withholding issue",
                severity="high",
                confidence="high",
                evidence=salary,
                explanation="Withholding wages or settlement requires a clear written basis and calculation.",
                suggested_next_step="Ask HR for a written full-and-final calculation and deduction basis.",
            )
        )

    for notice in _clauses(document, "notice_period"):
        days = _notice_days(notice)
        if days and days > 60:
            results.append(
                RuleResult(
                    id="employment_long_notice_period",
                    passed=False,
                    title="Notice period exceeds 60 days",
                    severity="medium",
                    confidence="high",
                    evidence=[notice],
                    explanation="A long notice period can affect exit options and should be checked against role, contract, HR policy, and state-specific rules.",
                    suggested_next_step="Compare the appointment letter with HR policy and ask whether buyout or waiver is available in writing.",
                )
            )

    arbitration = _clauses(document, "arbitration_clause")
    if arbitration and issue_type not in UNPAID_PAYMENT_ISSUES | CONTRACT_PAYMENT_REVIEW_ISSUES:
        results.append(
            RuleResult(
                id="employment_arbitration_path",
                passed=False,
                title="Arbitration clause may affect dispute path",
                severity="medium",
                confidence="medium",
                evidence=arbitration,
                explanation="Arbitration wording may affect forum and process. This is procedural information, not a prediction.",
                suggested_next_step="Preserve the arbitration clause and ask a lawyer/legal-aid clinic how it affects your next step.",
            )
        )

    if not jurisdiction.state:
        results.append(
            RuleResult(
                id="employment_jurisdiction_missing",
                passed=False,
                title="State or jurisdiction is missing",
                severity="medium",
                confidence="high",
                evidence=[],
                explanation="Employment rules can vary by state and worker category, so confidence is lower without location.",
                suggested_next_step="Provide work location, contract jurisdiction, and current city/state.",
            )
        )

    if document.document_type == "employment_document" and not any(
        "policy" in clause.raw_text.lower() for clause in document.extracted_clauses
    ):
        results.append(
            RuleResult(
                id="employment_hr_policy_missing",
                passed=False,
                title="HR policy or exit policy not provided",
                severity="medium",
                confidence="medium",
                evidence=[],
                explanation="Offer letters often do not contain the full exit process or deduction policy.",
                suggested_next_step="Upload the HR policy, exit policy, bond agreement, and any resignation emails.",
            )
        )

    if not results:
        results.append(
            RuleResult(
                id="employment_no_major_rule_flag",
                passed=True,
                title="No major deterministic employment risk flag",
                severity="low",
                confidence="medium",
                evidence=[],
                explanation="No high-risk employment clause was detected by the rule engine.",
            )
        )
    return results
