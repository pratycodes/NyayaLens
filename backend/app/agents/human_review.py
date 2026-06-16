from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.core.schemas import FinalReport, RiskFlag


class HumanReviewDecision(BaseModel):
    needed: bool
    reasons: list[str] = Field(default_factory=list)
    suggested_reviewer: str = "legal aid / qualified lawyer"


def _has_arbitration(report: FinalReport) -> bool:
    return any(
        clause.name == "arbitration_clause"
        for clause in report.extracted_facts.extracted_clauses
    )


def _reviewer_for_domain(domain: str) -> str:
    if domain == "employment":
        return "labour department/helpdesk or employment lawyer/legal aid"
    if domain == "tenancy":
        return "rent/civil authority, legal aid, or local tenancy lawyer"
    if domain == "contract_payment":
        return "civil/contract lawyer or legal aid"
    if domain == "safety":
        return "legal aid or local authority for urgent safety concerns"
    return "senior reviewer or legal aid"


def evaluate_human_review(report: FinalReport) -> HumanReviewDecision:
    reasons: list[str] = []
    risks: list[RiskFlag] = report.risk_flags
    if any(risk.severity == "high" for risk in risks):
        reasons.append("At least one high-severity risk is present.")
    if not report.jurisdiction.state:
        reasons.append("State or jurisdiction is unclear.")
    if _has_arbitration(report):
        reasons.append("An arbitration clause may affect the dispute path.")
    if report.issue_detected.unsafe_request or report.issue_detected.domain == "safety":
        reasons.append("The request has safety-sensitive handling requirements.")
    if "demo corpus" in " ".join(report.uncertainties).lower():
        reasons.append("Only demo corpus material is available; official source review is recommended.")
    sensitive_terms = " ".join(
        [
            report.issue_detected.issue_type,
            report.issue_detected.domain,
            *(risk.title for risk in risks),
        ]
    ).lower()
    if any(term in sensitive_terms for term in ["eviction", "harassment", "threat", "fraud"]):
        reasons.append("The issue may involve eviction, harassment, threats, or fraud-sensitive facts.")
    return HumanReviewDecision(
        needed=bool(reasons),
        reasons=sorted(set(reasons)),
        suggested_reviewer=_reviewer_for_domain(report.issue_detected.domain),
    )
