from __future__ import annotations

ISSUE_TO_LEGAL_AREAS = {
    "unpaid_compensation": ["contract_payment", "labour_classification"],
    "invoice_unpaid": ["contract_payment", "labour_classification"],
    "payment_withheld": ["contract_payment", "labour_classification"],
    "contract_payment_review": ["contract_payment"],
    "payment_deduction": ["contract_payment"],
    "unpaid_salary": ["labour_wage", "employment"],
    "full_and_final": ["labour_wage", "employment"],
    "bond_recovery": ["employment_contract", "contract_payment"],
    "non_compete": ["employment_contract", "restraint_review"],
    "deposit_deduction": ["tenancy_deposit"],
    "repair_dispute": ["tenancy_repairs"],
    "threat_blackmail": ["criminal_screening"],
    "forged_document": ["criminal_screening"],
    "unsafe_request": ["criminal_screening"],
    "public_authority_abuse": ["constitution_public_law", "grievance"],
}


def legal_areas_for_issue(issue_type: str) -> list[str]:
    return ISSUE_TO_LEGAL_AREAS.get(issue_type, [])
