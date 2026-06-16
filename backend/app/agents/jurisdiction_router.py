from __future__ import annotations

import re

from backend.app.core.constants import CITY_TO_STATE, INDIAN_STATES
from backend.app.core.schemas import DocumentAnalysis, JurisdictionResult, UserContext


def _title(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split())


def route_jurisdiction(text: str, document: DocumentAnalysis, context: UserContext) -> JurisdictionResult:
    warnings: list[str] = []
    city = context.city
    state = context.state
    lowered = text.lower()

    if not city:
        for known_city in CITY_TO_STATE:
            if re.search(rf"\b{re.escape(known_city)}\b", lowered):
                city = _title(known_city)
                break
    if not state and city and city.lower() in CITY_TO_STATE:
        state = CITY_TO_STATE[city.lower()]
    if not state:
        for known_state in INDIAN_STATES:
            if re.search(rf"\b{re.escape(known_state)}\b", lowered):
                state = _title(known_state)
                break

    jurisdiction_clause = next(
        (clause.raw_text for clause in document.extracted_clauses if clause.name == "jurisdiction_clause"),
        None,
    )
    if jurisdiction_clause and not city:
        clause_lower = jurisdiction_clause.lower()
        for known_city in CITY_TO_STATE:
            if known_city in clause_lower:
                city = _title(known_city)
                state = state or CITY_TO_STATE[known_city]
                break

    if not state:
        warnings.append("State is missing or uncertain; state-specific law may apply.")
    if jurisdiction_clause:
        warnings.append("A jurisdiction clause was detected; its effect needs legal review.")

    confidence = "high" if state and city else "medium" if state or jurisdiction_clause else "low"
    return JurisdictionResult(
        state=state,
        city=city,
        jurisdiction_clause=jurisdiction_clause,
        confidence=confidence,  # type: ignore[arg-type]
        warnings=warnings,
    )
