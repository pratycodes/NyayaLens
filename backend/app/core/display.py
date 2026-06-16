from __future__ import annotations

LABELS = {
    "contract_payment_review": "Contract payment review",
    "unpaid_compensation": "Unpaid compensation / pending payment",
    "freelance_service_agreement": "Freelance/service agreement",
    "contract_payment": "Contract payment",
    "employment": "Employment",
    "tenancy": "Tenancy",
    "unpaid_salary": "Unpaid salary",
    "freelance_agreement_review": "Freelance agreement review",
    "payment_deduction": "Payment deduction review",
    "deposit_deduction": "Security deposit deduction",
    "repair_dispute": "Repair / maintenance dispute",
    "eviction_notice": "Eviction notice",
    "rent_increase": "Rent increase",
    "lock_in_dispute": "Lock-in dispute",
    "employment_exit": "Employment exit",
    "bond_recovery": "Employment bond / training recovery",
    "notice_period": "Notice period",
    "non_compete": "Non-compete / restrictive covenant",
    "full_and_final": "Full-and-final settlement",
    "unsafe_request": "Unsafe request",
    "employment_document": "Employment document",
    "tenancy_document": "Tenancy/rent agreement",
    "contract_document": "Contract document",
    "plain_text_description": "Plain-text dispute description",
    "demo": "Demo",
    "official": "Official",
    "mixed": "Mixed",
    "user_uploaded": "User-uploaded",
    "unknown": "Unknown",
    "criminal_screening": "Criminal screening",
    "constitution_public_law": "Constitution / public law",
    "labour_classification": "Worker classification",
    "labour_wage": "Labour wage",
    "tenancy_deposit": "Tenancy deposit",
    "tenancy_repairs": "Tenancy repairs",
    "employment_contract": "Employment contract",
    "restraint_review": "Restrictive covenant review",
    "relevant_provision_found": "Potentially relevant provision",
    "possible_civil_breach": "Possible civil breach",
    "possible_statutory_non_compliance": "Possible statutory non-compliance",
    "possible_criminal_allegation": "Possible criminal allegation",
    "not_enough_facts": "Not enough facts",
}


def display_label(value: str | None) -> str:
    if not value:
        return "Unknown"
    return LABELS.get(value, value.replace("_", " ").strip().capitalize())
