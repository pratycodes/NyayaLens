from __future__ import annotations

from backend.app.agents.remedy_planner import plan_remedy
from backend.app.core.schemas import (
    DocumentAnalysis,
    IssueAnalysis,
    JurisdictionResult,
    RemedyPlan,
    RiskFlag,
    UserContext,
)


def route_remedy(
    issue: IssueAnalysis,
    risks: list[RiskFlag],
    context: UserContext,
    *,
    document: DocumentAnalysis | None = None,
    jurisdiction: JurisdictionResult | None = None,
) -> RemedyPlan:
    remedy = plan_remedy(issue, risks, context)
    if document and any(clause.name == "arbitration_clause" for clause in document.extracted_clauses):
        arbitration_step = (
            "Review the arbitration or dispute-resolution clause before escalation; ask legal aid or a "
            "lawyer how it affects the practical route."
        )
        if arbitration_step not in remedy.steps:
            remedy.steps.append(arbitration_step)
    if jurisdiction and not jurisdiction.state:
        jurisdiction_step = "Confirm the state/city and contract jurisdiction before choosing a filing or escalation route."
        if jurisdiction_step not in remedy.steps:
            remedy.steps.append(jurisdiction_step)
    return remedy
