from __future__ import annotations

from backend.app.core.schemas import DocumentAnalysis, UserContext
from backend.app.legal_matcher.consistency_filters import (
    has_criminal_screening_facts,
    has_public_law_context,
)
from backend.app.legal_matcher.missing_fact_generator import missing_facts_for_area


def _clause_names(document: DocumentAnalysis) -> set[str]:
    return {clause.name for clause in document.extracted_clauses}


def _clause_texts(document: DocumentAnalysis, names: set[str]) -> list[str]:
    return [
        clause.raw_text
        for clause in document.extracted_clauses
        if clause.name in names
    ]


def matched_facts_for_area(
    legal_area: str,
    *,
    document: DocumentAnalysis,
    context: UserContext,
    user_text: str,
) -> list[str]:
    names = _clause_names(document)
    facts: list[str] = []
    if legal_area == "contract_payment":
        if document.document_type == "freelance_service_agreement":
            facts.append("uploaded document appears to be a freelance/service agreement")
        if names.intersection({"invoice_clause", "payment_timing_clause", "consideration_clause", "compensation_clause", "tds_clause"}):
            facts.extend(_clause_texts(document, {"invoice_clause", "payment_timing_clause", "consideration_clause", "compensation_clause", "tds_clause"})[:4])
        if user_text.strip():
            facts.append(f"user text: {user_text.strip()}")
    elif legal_area == "labour_classification":
        if "independent_contractor_clause" in names:
            facts.extend(_clause_texts(document, {"independent_contractor_clause"})[:2])
        if context.user_role:
            facts.append(f"user role: {context.user_role}")
    elif legal_area == "criminal_screening" and has_criminal_screening_facts(user_text):
        facts.append(f"user text contains criminal-screening fact pattern: {user_text.strip()}")
    elif legal_area in {"constitution_public_law", "grievance"} and has_public_law_context(context, user_text):
        facts.append(f"public authority context: {' '.join([context.counterparty or '', user_text]).strip()}")
    elif legal_area == "tenancy_deposit":
        if names.intersection({"security_deposit", "painting_cleaning_charges", "repairs_maintenance"}):
            facts.extend(_clause_texts(document, {"security_deposit", "painting_cleaning_charges", "repairs_maintenance"})[:3])
        if user_text.strip():
            facts.append(f"user text: {user_text.strip()}")
    return facts


def missing_facts_after_matching(legal_area: str, matched_facts: list[str]) -> list[str]:
    if legal_area == "contract_payment":
        lowered = " ".join(matched_facts).lower()
        missing = []
        for fact in missing_facts_for_area(legal_area):
            if fact in {"invoice copy", "payment due date", "written follow-up"} or fact.split()[0] not in lowered:
                missing.append(fact)
        return missing
    return missing_facts_for_area(legal_area)


def clause_present(document: DocumentAnalysis, clause_name: str) -> bool:
    return any(clause.name == clause_name for clause in document.extracted_clauses)
