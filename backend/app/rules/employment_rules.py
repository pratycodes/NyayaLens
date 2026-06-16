from __future__ import annotations

import re

from backend.app.core.schemas import DocumentAnalysis, JurisdictionResult, RuleResult, UserContext


def _clauses(document: DocumentAnalysis, name: str) -> list[str]:
    return [clause.raw_text for clause in document.extracted_clauses if clause.name == name]


def _notice_days(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(day|days|month|months)", text, flags=re.IGNORECASE)
    if not match:
        return None
    value = int(match.group(1))
    return value * 30 if match.group(2).lower().startswith("month") else value


def evaluate_employment_rules(
    document: DocumentAnalysis,
    context: UserContext,
    jurisdiction: JurisdictionResult,
    issue_type: str,
) -> list[RuleResult]:
    results: list[RuleResult] = []
    query = (context.query or "").lower()

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
    if arbitration:
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
