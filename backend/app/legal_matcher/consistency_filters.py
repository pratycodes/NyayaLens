from __future__ import annotations

from backend.app.core.schemas import DocumentAnalysis, UserContext

CRIMINAL_TRIGGER_TERMS = {
    "forged invoice",
    "forged document",
    "fake signature",
    "threat",
    "intimidation",
    "blackmail",
    "deception from beginning",
    "dishonest inducement",
    "physical intimidation",
    "theft",
    "misappropriation",
    "fraud",
}

CRIMINAL_NON_TRIGGERS = {
    "payment delayed",
    "tds",
    "deducted",
    "damages",
    "arbitration",
    "jurisdiction",
}

PUBLIC_AUTHORITY_TERMS = {
    "government",
    "public authority",
    "public official",
    "statutory authority",
    "municipal",
    "police",
    "labour department",
    "state action",
    "government scheme",
    "public benefit",
    "fundamental rights",
}


def has_criminal_screening_facts(user_text: str) -> bool:
    lowered = user_text.lower()
    return any(term in lowered for term in CRIMINAL_TRIGGER_TERMS)


def has_public_law_context(context: UserContext, user_text: str) -> bool:
    lowered = " ".join([context.counterparty or "", user_text]).lower()
    return any(term in lowered for term in PUBLIC_AUTHORITY_TERMS)


def should_exclude_legal_area(
    legal_area: str,
    *,
    document: DocumentAnalysis,
    context: UserContext,
    user_text: str,
) -> bool:
    if legal_area == "criminal_screening":
        return not has_criminal_screening_facts(user_text)
    if legal_area in {"constitution_public_law", "grievance"}:
        return not has_public_law_context(context, user_text)
    return legal_area.startswith("tenancy") and document.document_type == "freelance_service_agreement"
