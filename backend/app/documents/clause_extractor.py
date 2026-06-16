from __future__ import annotations

import re
from dataclasses import dataclass

from backend.app.core.schemas import DocumentAnalysis, ExtractedClause
from backend.app.documents.document_classifier import classify_document


@dataclass(frozen=True)
class ClausePattern:
    name: str
    pattern: str
    risk_hint: str | None = None
    confidence: str = "medium"


EMPLOYMENT_PATTERNS = [
    ClausePattern("notice_period", r"(?:notice period|serve notice)[^.\n]*(?:\d+\s*(?:day|days|month|months))[^.\n]*", "Long notice periods can affect exit planning."),
    ClausePattern("bond_amount", r"(?:bond|service bond|training bond)[^.\n]*(?:₹|rs\.?|inr)\s?[\d,]+[^.\n]*", "Bond recovery needs proof of actual loss/training cost."),
    ClausePattern("training_cost", r"(?:training cost|training expenses|cost of training)[^.\n]*(?:₹|rs\.?|inr)\s?[\d,]+[^.\n]*", "Training recovery should be itemized."),
    ClausePattern("non_compete_duration", r"(?:non[- ]compete|not compete)[^.\n]*(?:\d+\s*(?:month|months|year|years))[^.\n]*", "Post-employment non-compete clauses need legal review."),
    ClausePattern("non_solicit_duration", r"(?:non[- ]solicit|not solicit)[^.\n]*(?:\d+\s*(?:month|months|year|years))[^.\n]*", "Non-solicit scope and duration may matter."),
    ClausePattern("confidentiality_clause", r"(?:confidentiality|confidential information)[^.\n]*", "Confidentiality obligations can survive exit."),
    ClausePattern("full_and_final_settlement", r"(?:full[- ]and[- ]final|fnf|final settlement)[^.\n]*", "Final settlement wording affects deductions and release."),
    ClausePattern("salary_withholding", r"(?:withhold|withholding|deduct|deduction)[^.\n]*(?:salary|wages|payment|settlement)[^.\n]*", "Salary withholding should have a written basis."),
    ClausePattern("relieving_letter", r"(?:relieving letter|experience letter|service certificate)[^.\n]*", "Relieving documents are often practically important for future employment."),
    ClausePattern("arbitration_clause", r"(?:arbitration|arbitrator)[^.\n]*", "Arbitration can affect the dispute path."),
    ClausePattern("jurisdiction_clause", r"(?:jurisdiction|courts? at|venue)[^.\n]*(?:bengaluru|bangalore|mumbai|delhi|pune|hyderabad|chennai|kolkata|karnataka|maharashtra|haryana|telangana|tamil nadu|west bengal|india)[^.\n]*", "Jurisdiction clause may affect where disputes are raised."),
    ClausePattern("termination_clause", r"(?:termination|terminate)[^.\n]*", "Termination wording affects exit rights and obligations."),
    ClausePattern("probation_clause", r"(?:probation|probationary)[^.\n]*", "Probation can change notice and confirmation status."),
]

TENANCY_PATTERNS = [
    ClausePattern("rent_amount", r"(?:monthly rent|rent)[^.\n]*(?:₹|rs\.?|inr)\s?[\d,]+[^.\n]*", "Rent amount anchors deposit and increase disputes."),
    ClausePattern("security_deposit", r"(?:security deposit|deposit)[^.\n]*(?:₹|rs\.?|inr|\d+\s*months?)[^.\n]*", "Deposit deductions should be itemized."),
    ClausePattern("lock_in_period", r"(?:lock[- ]in|lock in)[^.\n]*(?:\d+\s*(?:month|months|year|years))[^.\n]*", "Lock-in enforceability depends on agreement and local law."),
    ClausePattern("notice_period", r"(?:notice period|written notice|prior notice)[^.\n]*(?:\d+\s*(?:day|days|month|months))[^.\n]*", "Notice requirements should be checked before exit or eviction."),
    ClausePattern("rent_increase", r"(?:increase|enhancement|hike)[^.\n]*(?:rent)[^.\n]*", "Rent increase should follow agreement and applicable law."),
    ClausePattern("repairs_maintenance", r"(?:repair|maintenance|fixture|damage)[^.\n]*", "Repair responsibility often turns on evidence and agreement wording."),
    ClausePattern("painting_cleaning_charges", r"(?:painting|cleaning)[^.\n]*(?:charge|deduct|cost|expense)[^.\n]*", "Standard deductions should be supported by agreement or bills."),
    ClausePattern("eviction_clause", r"(?:evict|eviction|vacate|terminate tenancy)[^.\n]*", "Eviction generally needs written process."),
    ClausePattern("police_verification", r"(?:police verification|tenant verification)[^.\n]*", "Local compliance obligations may apply."),
    ClausePattern("arbitration_clause", r"(?:arbitration|arbitrator)[^.\n]*", "Arbitration can affect the dispute path."),
    ClausePattern("jurisdiction_clause", r"(?:jurisdiction|courts? at|venue)[^.\n]*(?:bengaluru|bangalore|mumbai|delhi|pune|hyderabad|chennai|kolkata|karnataka|maharashtra|haryana|telangana|tamil nadu|west bengal|india)[^.\n]*", "Jurisdiction clause may affect where disputes are raised."),
]

DATE_RE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Z][a-z]+\s+\d{4}|[A-Z][a-z]+\s+\d{1,2},\s+\d{4})\b")
AMOUNT_RE = re.compile(r"(?:₹|Rs\.?|INR)\s?[\d,]+(?:\.\d+)?", re.IGNORECASE)
PARTY_RE = re.compile(r"\b(?:between|by and between)\s+([^.\n]+?)\s+and\s+([^.\n]+?)(?:\.|\n|$)", re.IGNORECASE)


def _normalize_value(raw: str) -> str:
    amount = AMOUNT_RE.search(raw)
    if amount:
        return amount.group(0)
    duration = re.search(r"\b\d+\s*(?:day|days|month|months|year|years)\b", raw, re.IGNORECASE)
    if duration:
        return duration.group(0)
    return raw.strip()[:120]


def _line_page_map(page_texts: list[tuple[int, str]] | None) -> list[tuple[int, str]]:
    if not page_texts:
        return [(1, "")]
    return page_texts


def _extract_patterns(
    text: str,
    patterns: list[ClausePattern],
    page_texts: list[tuple[int, str]] | None,
) -> list[ExtractedClause]:
    clauses: list[ExtractedClause] = []
    seen: set[tuple[str, str]] = set()
    pages = _line_page_map(page_texts)
    for pattern in patterns:
        for match in re.finditer(pattern.pattern, text, flags=re.IGNORECASE):
            raw = " ".join(match.group(0).split())
            key = (pattern.name, raw.lower())
            if key in seen:
                continue
            seen.add(key)
            page_number = None
            for page, page_text in pages:
                if raw[:50].lower() in " ".join(page_text.split()).lower():
                    page_number = page
                    break
            clauses.append(
                ExtractedClause(
                    name=pattern.name,
                    value=_normalize_value(raw),
                    raw_text=raw,
                    page=page_number,
                    confidence=pattern.confidence,  # type: ignore[arg-type]
                    risk_hint=pattern.risk_hint,
                )
            )
    return clauses


def extract_document_analysis(
    text: str,
    *,
    page_texts: list[tuple[int, str]] | None = None,
    parser_warnings: list[str] | None = None,
) -> DocumentAnalysis:
    document_type, domain, _confidence = classify_document(text)
    patterns = EMPLOYMENT_PATTERNS + TENANCY_PATTERNS
    if domain == "employment":
        patterns = EMPLOYMENT_PATTERNS
    elif domain == "tenancy":
        patterns = TENANCY_PATTERNS
    clauses = _extract_patterns(text, patterns, page_texts)

    dates = sorted(set(DATE_RE.findall(text)))
    amounts = sorted(set(match.group(0) for match in AMOUNT_RE.finditer(text)))
    parties: list[str] = []
    party_match = PARTY_RE.search(text)
    if party_match:
        parties = [" ".join(party_match.group(1).split()), " ".join(party_match.group(2).split())]

    missing_fields: list[str] = []
    if domain == "unknown":
        missing_fields.append("dispute domain")
    if not any(clause.name == "jurisdiction_clause" for clause in clauses):
        missing_fields.append("state/city or jurisdiction")
    if not dates:
        missing_fields.append("document date")

    return DocumentAnalysis(
        document_type=document_type,
        extracted_clauses=clauses,
        parties=parties,
        dates=dates,
        amounts=amounts,
        detected_domain=domain,  # type: ignore[arg-type]
        missing_fields=missing_fields,
        parser_warnings=parser_warnings or [],
    )
