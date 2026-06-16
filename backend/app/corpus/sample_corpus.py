from __future__ import annotations

from pathlib import Path

from backend.app.config import get_settings

DEMO_PREFIX = (
    "DEMO CORPUS: This is a simplified educational placeholder. "
    "Replace with official legal sources before real-world use."
)


SAMPLE_FILES = {
    "employment/employment_general_information.txt": f"""{DEMO_PREFIX}

Employment Exit General Information

Employees should preserve offer letters, employment contracts, HR policies, resignation emails, payslips, attendance records, and written communication about final settlement. A dispute about unpaid wages or final settlement should be documented in writing with a request for calculation details.

Employment bonds and training cost recovery are contract issues. A fair assessment usually depends on the text of the agreement, proof of actual training expenses, the employee's role, timing of resignation, and whether the claimed amount is a penalty or a genuine pre-estimate of loss. This demo source does not state any exact section number.

Post-employment non-compete restrictions need careful legal review. Broad restrictions after employment may be difficult to enforce, but confidentiality and non-solicitation obligations can still matter depending on facts and contract wording.

Long notice periods should be checked against the signed contract, appointment letter, role category, company policy, and applicable state-specific employment law. If jurisdiction is unclear, confidence should be reduced.
""",
    "employment/contract_general_information.txt": f"""{DEMO_PREFIX}

Contract Clause General Information

Arbitration clauses may affect the forum or process for dispute resolution. Jurisdiction clauses may identify a city or court, but their effect depends on the contract and applicable law.

For deductions, recovery, or withholding clauses, ask for the written clause, itemized calculation, proof of loss or expense, and the legal basis for deduction. Avoid verbal-only communication and preserve copies of all notices and replies.

This educational source is not a substitute for official statutes, rules, notifications, judgments, or advice from a qualified lawyer.
""",
    "tenancy/tenancy_general_information.txt": f"""{DEMO_PREFIX}

Tenancy General Information

Tenants and landlords should preserve the rent agreement, rent receipts, deposit proof, move-in and move-out photos, inventory lists, repair bills, messages, and written notices.

Security deposit deductions should be explained with an itemized basis such as unpaid rent, documented damage, agreed painting charges, or repair invoices. Where the agreement is unclear or no itemized bill is provided, the dispute needs careful evidence review.

Eviction or forced lockout issues are sensitive. Parties should avoid self-help confrontation, lock-breaking, threats, or harassment. Written notice, agreement terms, and state-specific rent or tenancy rules may matter.

Rent increase, lock-in period, repairs, and maintenance disputes depend on the agreement, local law, notices, and evidence of condition or payment.
""",
    "tenancy/legal_aid_general_information.txt": f"""{DEMO_PREFIX}

Legal Aid and Safety General Information

For high-risk employment or tenancy disputes, consider speaking with a qualified lawyer, legal aid clinic, district legal services authority, labour department helpdesk, or appropriate local rent/civil authority depending on the state and facts.

Do not forge evidence, impersonate officials or lawyers, threaten the other party, blackmail, break locks, or publish private information. Use written, polite, factual communication and keep records.

This demo source intentionally avoids promising outcomes or naming exact portals because procedures vary by state and change over time.
""",
}


def ensure_sample_corpus() -> list[Path]:
    settings = get_settings()
    created: list[Path] = []
    for relative, content in SAMPLE_FILES.items():
        path = settings.raw_laws_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
        created.append(path)
    return created
