from __future__ import annotations

from backend.app.legal_ontology.legal_elements import (
    CLASSIFICATION_MISSING_FACTS,
    CRIMINAL_SCREENING_FACTS,
    PAYMENT_MISSING_FACTS,
    PUBLIC_LAW_FACTS,
)


def missing_facts_for_area(legal_area: str) -> list[str]:
    if legal_area == "contract_payment":
        return PAYMENT_MISSING_FACTS
    if legal_area == "labour_classification":
        return CLASSIFICATION_MISSING_FACTS
    if legal_area == "criminal_screening":
        return CRIMINAL_SCREENING_FACTS
    if legal_area in {"constitution_public_law", "grievance"}:
        return PUBLIC_LAW_FACTS
    if legal_area == "tenancy_deposit":
        return ["itemized deductions", "deposit proof", "move-in/move-out condition", "repair bills/photos"]
    return ["complete facts and supporting documents"]
