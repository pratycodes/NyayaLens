from __future__ import annotations

LEGAL_AREA_TO_ISSUE_TAGS = {
    "contract_payment": ["contract_payment", "unpaid_compensation", "invoice_unpaid", "payment_deduction"],
    "labour_classification": ["labour_classification", "unpaid_compensation", "unpaid_salary"],
    "labour_wage": ["labour_wage", "unpaid_salary", "full_and_final"],
    "employment": ["labour_wage", "employment_contract"],
    "employment_contract": ["employment_contract", "contract_payment"],
    "restraint_review": ["restraint_review", "employment_contract"],
    "tenancy_deposit": ["tenancy_deposit", "deposit_deduction"],
    "tenancy_repairs": ["tenancy_repairs", "repair_dispute"],
    "criminal_screening": ["criminal_screening", "forged_document", "threat_blackmail", "fraud"],
    "constitution_public_law": ["constitution_public_law", "public_authority_abuse", "state_action"],
    "grievance": ["grievance", "constitution_public_law"],
}


def tags_for_legal_area(area: str) -> list[str]:
    return LEGAL_AREA_TO_ISSUE_TAGS.get(area, [area])
