from __future__ import annotations

from backend.app.core.schemas import DocumentAnalysis, JurisdictionResult, RuleResult, UserContext


def _clauses(document: DocumentAnalysis, name: str) -> list[str]:
    return [clause.raw_text for clause in document.extracted_clauses if clause.name == name]


def evaluate_tenancy_rules(
    document: DocumentAnalysis,
    context: UserContext,
    jurisdiction: JurisdictionResult,
    issue_type: str,
) -> list[RuleResult]:
    results: list[RuleResult] = []
    query = (context.query or "").lower()

    deposit = _clauses(document, "security_deposit")
    if deposit and any(word in query for word in ["deduct", "deposit", "refund", "bill", "itemized"]):
        severity = "high" if "bill" in query or "without" in query else "medium"
        results.append(
            RuleResult(
                id="tenancy_deposit_itemization",
                passed=False,
                title="Security deposit deduction needs itemized basis",
                severity=severity,  # type: ignore[arg-type]
                confidence="high",
                evidence=deposit,
                explanation="Deposit deductions should be supported by agreement wording, documented damage, dues, or itemized bills.",
                suggested_next_step="Ask the landlord for itemized deductions, bills, photos, and move-out condition notes.",
            )
        )

    eviction = _clauses(document, "eviction_clause")
    if eviction or issue_type == "eviction_notice":
        verbal_only = any(word in query for word in ["verbal", "phone", "whatsapp only", "no written"])
        results.append(
            RuleResult(
                id="tenancy_eviction_written_notice",
                passed=False,
                title="Eviction or vacation issue needs written process",
                severity="high" if verbal_only else "medium",
                confidence="high" if verbal_only else "medium",
                evidence=eviction,
                explanation="Eviction/vacation disputes are sensitive and should be handled through written communication and applicable local process.",
                suggested_next_step="Ask for written notice and avoid confrontation, lock-breaking, or self-help steps.",
            )
        )

    lock_in = _clauses(document, "lock_in_period")
    if lock_in:
        results.append(
            RuleResult(
                id="tenancy_lock_in_review",
                passed=False,
                title="Lock-in clause detected",
                severity="medium",
                confidence="high",
                evidence=lock_in,
                explanation="Lock-in consequences depend on the agreement, local law, and reason for exit.",
                suggested_next_step="Check start date, exit date, penalty wording, and communications before deciding.",
            )
        )

    rent_increase = _clauses(document, "rent_increase")
    if rent_increase or issue_type == "rent_increase":
        results.append(
            RuleResult(
                id="tenancy_rent_increase_clause",
                passed=False,
                title="Rent increase issue detected",
                severity="medium",
                confidence="medium",
                evidence=rent_increase,
                explanation="Rent increase disputes depend on agreement wording, written notice, and state-specific rules.",
                suggested_next_step="Ask for the written clause or notice relied on for the increase.",
            )
        )

    repairs = _clauses(document, "repairs_maintenance") + _clauses(document, "painting_cleaning_charges")
    if repairs or issue_type == "repair_dispute":
        results.append(
            RuleResult(
                id="tenancy_repair_evidence",
                passed=False,
                title="Repair or maintenance evidence needed",
                severity="medium",
                confidence="medium",
                evidence=repairs,
                explanation="Repair responsibility often turns on proof of condition, cause, bills, and agreement wording.",
                suggested_next_step="Collect photos, move-in report, receipts, messages, and repair estimates.",
            )
        )

    if not jurisdiction.state:
        results.append(
            RuleResult(
                id="tenancy_jurisdiction_missing",
                passed=False,
                title="State or jurisdiction is missing",
                severity="medium",
                confidence="high",
                evidence=[],
                explanation="Tenancy and rent procedures can be state-specific, so confidence is lower without location.",
                suggested_next_step="Provide city/state and the jurisdiction clause if available.",
            )
        )

    if not results:
        results.append(
            RuleResult(
                id="tenancy_no_major_rule_flag",
                passed=True,
                title="No major deterministic tenancy risk flag",
                severity="low",
                confidence="medium",
                evidence=[],
                explanation="No high-risk tenancy clause was detected by the rule engine.",
            )
        )
    return results
