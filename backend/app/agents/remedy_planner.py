from __future__ import annotations

from backend.app.core.schemas import IssueAnalysis, RemedyPlan, RiskFlag, UserContext

EMPLOYMENT_EVIDENCE = [
    "Employment contract or offer letter",
    "Training/bond agreement and training invoices if any",
    "HR policy or exit policy",
    "Payslips, bank credits, and full-and-final calculation",
    "Resignation email, acceptance, and last working day communication",
    "Relieving letter or experience letter correspondence",
]

TENANCY_EVIDENCE = [
    "Rent agreement and renewal addenda",
    "Deposit payment proof and rent receipts",
    "Move-in and move-out photos/videos",
    "Repair bills, inspection notes, and itemized deductions",
    "Messages, emails, and written notices",
    "Police verification or society communications if relevant",
]


def _employment_draft() -> str:
    return (
        "Subject: Request for written clarification on exit settlement\n\n"
        "Dear HR Team,\n\n"
        "I am writing to request a written breakdown of the amounts proposed to be adjusted in my exit settlement, "
        "including the clause relied on, itemized calculation, and supporting documents for any recovery or deduction. "
        "Please also confirm the status of my relieving/experience letter and any pending exit formalities.\n\n"
        "Regards,\n[Your Name]"
    )


def _tenancy_draft() -> str:
    return (
        "Hello,\n\n"
        "Please share an itemized written statement for the proposed security deposit deductions, including photos, "
        "bills/receipts, and the agreement clause relied on. I would also appreciate confirmation of the refundable "
        "balance and expected payment date.\n\n"
        "Regards,\n[Your Name]"
    )


def plan_remedy(issue: IssueAnalysis, risks: list[RiskFlag], context: UserContext) -> RemedyPlan:
    if issue.unsafe_request:
        return RemedyPlan(
            steps=[
                "Do not use threats, forged evidence, impersonation, or confrontation.",
                "Preserve the original documents and communication records.",
                "Use a short written clarification request and seek legal aid for urgent risks.",
            ],
            evidence_checklist=["Original documents", "Messages/emails", "Payment records", "Notices"],
            draft_message=(
                "I want to resolve this through written communication. Please share the facts, documents, "
                "and calculation you are relying on so I can respond appropriately."
            ),
            escalation_note="For immediate safety concerns, contact local authorities or qualified legal aid.",
        )

    high_risk = any(risk.severity == "high" for risk in risks)
    if issue.domain == "employment":
        steps = [
            "Preserve the contract, offer letter, HR policy, payslips, and resignation emails.",
            "Ask HR for a written calculation and the clause relied on for any recovery or deduction.",
            "Avoid verbal-only communication; confirm calls in a follow-up email.",
            "Do not concede liability for a bond or non-compete without reviewing the agreement and evidence.",
        ]
        if high_risk:
            steps.append("Consult a lawyer or legal-aid clinic before signing undertakings or settlement releases.")
        steps.append("If wages are withheld, consider a labour department/legal-aid route depending on state and worker category.")
        return RemedyPlan(
            steps=steps,
            evidence_checklist=EMPLOYMENT_EVIDENCE,
            draft_message=_employment_draft(),
            escalation_note="Use legal-aid or labour routes carefully because state and worker-category rules may apply.",
        )

    if issue.domain == "tenancy":
        steps = [
            "Preserve the rent agreement, receipts, messages, notices, and property-condition evidence.",
            "Ask the landlord for itemized deposit deductions with bills and photos.",
            "Communicate in writing and keep the tone factual.",
            "Avoid self-help eviction, lock-breaking, threats, or confrontation.",
        ]
        if high_risk:
            steps.append("Consult legal aid or a local lawyer before vacating under pressure or accepting large deductions.")
        steps.append("Consider the appropriate rent/civil authority route depending on state and facts.")
        return RemedyPlan(
            steps=steps,
            evidence_checklist=TENANCY_EVIDENCE,
            draft_message=_tenancy_draft(),
            escalation_note="Tenancy procedures vary by state; confirm the local route before filing.",
        )

    return RemedyPlan(
        steps=[
            "Provide the dispute domain, city/state, user role, counterparty, and key dates.",
            "Upload the signed agreement and any notices or payment records.",
            "Use written, polite clarification before escalation.",
        ],
        evidence_checklist=["Agreement", "Notices", "Payment proof", "Messages/emails"],
        draft_message="Please share the written basis, calculation, and supporting documents for your position.",
        escalation_note="The system needs more facts before suggesting a domain-specific route.",
    )
