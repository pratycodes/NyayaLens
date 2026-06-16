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

CONTRACTOR_PAYMENT_EVIDENCE = [
    "Service agreement",
    "Scope of work",
    "Invoice or payment request",
    "Proof of work delivered",
    "Emails/messages assigning or accepting work",
    "Payment reminders",
    "Bank records",
    "TDS/deduction communication",
    "Written reason for withholding payment, if any",
]

EMPLOYEE_PAYMENT_EVIDENCE = [
    "Offer letter or appointment letter",
    "Payslips, attendance records, and bank credits",
    "Resignation, full-and-final, or payroll communication",
    "Written reason for withholding payment if any",
    "Payment follow-ups already sent",
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


def _contractor_payment_draft() -> str:
    return (
        "Subject: Request for written update on pending payment\n\n"
        "Dear [Company/Client/Accounts Team],\n\n"
        "I am writing to request a written update on the pending payment for my work/services. "
        "Please share the amount currently payable, the expected payment date, and any reason or "
        "document relied on for withholding, adjusting, or deducting any amount. I would also "
        "appreciate an itemized calculation if any deduction is proposed.\n\n"
        "Regards,\n[Your Name]"
    )


def _contractor_payment_review_draft() -> str:
    return (
        "Subject: Request for written clarification on payment terms\n\n"
        "Dear [Company/Client/Accounts Team],\n\n"
        "I am writing to request a written clarification of the payment terms under our service "
        "agreement, including the invoice process, expected payment date, and any deduction or "
        "adjustment that may apply. Please also share an itemized calculation if any amount is "
        "proposed to be withheld or adjusted.\n\n"
        "Regards,\n[Your Name]"
    )


def _employee_payment_draft() -> str:
    return (
        "Subject: Request for written clarification on pending salary/settlement\n\n"
        "Dear HR/Payroll Team,\n\n"
        "I am writing to request a written update on my pending salary or settlement payment. "
        "Please share the amount currently payable, the expected payment date, and the reason or "
        "document relied on for any withholding, adjustment, or deduction. I would also appreciate "
        "an itemized calculation if any deduction is proposed.\n\n"
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
    if issue.domain in {"employment", "contract_payment"}:
        user_role = (context.user_role or "").strip().lower()
        is_contractor_like = user_role in {
            "contractor",
            "freelancer",
            "consultant",
            "service provider",
        }
        is_unpaid_payment_issue = issue.issue_type in {
            "unpaid_salary",
            "full_and_final",
            "unpaid_compensation",
            "payment_withheld",
            "invoice_unpaid",
        }
        is_contract_review_issue = issue.issue_type in {
            "payment_deduction",
            "contract_payment_review",
            "freelance_agreement_review",
        }
        if (
            is_unpaid_payment_issue
            or is_contract_review_issue
            or (issue.domain == "contract_payment" and user_role != "employee")
        ):
            if is_contractor_like or issue.domain == "contract_payment":
                return RemedyPlan(
                    steps=[
                        "Preserve the service agreement, invoices, work delivery proof, emails, payment reminders, and bank records.",
                        "Ask the company/client for a written payment status.",
                        "Ask for an itemized calculation if any deduction or adjustment is proposed.",
                        "Clarify whether any deduction is TDS, contractual adjustment, penalty, or disputed withholding.",
                        "Avoid verbal-only communication; confirm calls in writing.",
                        "Clarify whether the amount is salary, invoice, stipend, consulting fee, or full-and-final settlement.",
                        "Consider legal aid or an appropriate civil/contract/labour route depending on worker classification and state.",
                    ],
                    evidence_checklist=CONTRACTOR_PAYMENT_EVIDENCE,
                    draft_message=(
                        _contractor_payment_draft()
                        if is_unpaid_payment_issue
                        else _contractor_payment_review_draft()
                    ),
                    escalation_note=(
                        "The route may depend on whether this is an employment, contractor, consulting, "
                        "freelance, or civil contract payment dispute."
                    ),
                )
            return RemedyPlan(
                steps=[
                    "Preserve offer letter, appointment letter, payslips, attendance records, bank credits, and resignation/FNF communication.",
                    "Ask HR/payroll for a written calculation and expected payment date.",
                    "Request the written reason for withholding or adjusting payment.",
                    "Send a polite written follow-up and preserve the response.",
                    "Consider labour/legal-aid route depending on worker category and state.",
                ],
                evidence_checklist=EMPLOYEE_PAYMENT_EVIDENCE,
                draft_message=_employee_payment_draft(),
                escalation_note="Employment payment routes can vary by worker category and state.",
            )
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
