from __future__ import annotations

import re
import string
from dataclasses import dataclass

from backend.app.core.constants import CITY_TO_STATE
from backend.app.core.schemas import DocumentAnalysis, ExtractedClause, InferredContextValue
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

CONTRACT_PAYMENT_PATTERNS = [
    ClausePattern("freelancer_role", r"(?:freelancer|project manager|consultant|contractor)[^.\n]*", "Role/category matters for payment route selection."),
    ClausePattern("consideration_clause", r"(?:consideration|compensation details)[^.\n]*", "Consideration/payment wording anchors the claim."),
    ClausePattern("invoice_clause", r"(?:invoice)[^.\n]*(?:generated|raised|billing|payment|month)[^.\n]*", "Invoice timing can determine due date and evidence."),
    ClausePattern("payment_timing_clause", r"(?:payment shall be made|payment will be made|payment is due|payment[^.\n]*(?:last week|within\s+\d+\s+days|due date))[^.\n]*", "Payment timing can show when the amount became due."),
    ClausePattern("compensation_clause", r"(?:pro[- ]rata compensation|initial compensation|compensation details|compensation)[^.\n]*(?:\d[\d,]*(?:\s*/-)?(?:\s+\d[\d,]*(?:\s*/-)?)?)?[^.\n]*", "Compensation table or amount should be compared with unpaid amount."),
    ClausePattern("pro_rata_compensation_clause", r"(?:pro[- ]rata compensation|pro[- ]rata data month)[^.\n]*", "Pro-rata wording should be compared with the actual work period."),
    ClausePattern("tds_clause", r"(?:tds|tax deducted at source)[^.\n]*", "TDS wording may affect net payable amount."),
    ClausePattern("independent_contractor_clause", r"(?:independent contractors?|independent contractor relationship)[^.\n]*", "Worker classification can affect remedy route."),
    ClausePattern("termination_notice_clause", r"(?:one\s+month(?:'s|s)?\s+written\s+notice|termination notice)[^.\n]*", "Termination notice can affect final payment timing."),
    ClausePattern("termination_clause", r"(?:one\s+month(?:'s|s)?\s+written\s+notice|termination notice|terminate this agreement|termination of this agreement)[^.\n]*", "Termination wording can affect final payment or notice."),
    ClausePattern("arbitration_clause", r"(?:arbitration|arbitrator)[^.\n]*", "Arbitration can affect dispute path."),
    ClausePattern("jurisdiction_clause", r"(?:jurisdiction|courts? at|exclusive jurisdiction|venue)[^.\n]*(?:bengaluru|bangalore|mumbai|delhi|pune|hyderabad|chennai|kolkata|karnataka|maharashtra|haryana|telangana|tamil nadu|west bengal|india)[^.\n]*", "Jurisdiction clause may affect where disputes are raised."),
]

DATE_RE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Z][a-z]+,?\s+\d{4}|[A-Z][a-z]+\s+\d{1,2},\s+\d{4})\b")
AMOUNT_RE = re.compile(r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d+)?(?:/-)?", re.IGNORECASE)
BROKEN_AMOUNT_RE = re.compile(r"^(?:₹|rs\.?|inr|/-|rs,)$", re.IGNORECASE)
PARTY_RE = re.compile(r"\b(?:between|by and between)\s+([^.\n]+?)\s+and\s+([^.\n]+?)(?:\.|\n|$)", re.IGNORECASE)
BARE_AMOUNT_CONTEXT_RE = re.compile(
    r"\b(?:initial compensation|compensation|pro[- ]rata|payment|invoice|consideration|tds)[^\n]*",
    re.IGNORECASE,
)
BARE_NUMBER_RE = re.compile(r"\b(?:\d{5,}|\d{1,3}(?:,\d{3})+)(?:/-)?(?=\s|$|[.,;])")
COMPANY_RE = re.compile(
    r"\b([A-Z][A-Z0-9&.,'() -]{2,}?\s+(?:LLP|PRIVATE\s+LIMITED|PVT\.?\s+LTD\.?|LIMITED))\b",
    re.IGNORECASE,
)
FREELANCER_NAME_PATTERNS = [
    re.compile(
        r"\bAND\s+([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,4})\s+(?:as\s+a\s+)?(?:Freelancer|Consultant|Contractor)\b"
    ),
    re.compile(
        r"\bAND\s+([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,4})\s*,?\s*hereinafter\s+referred\s+to\s+as\s+the\s+\"?Freelancer",
        re.IGNORECASE,
    ),
    re.compile(
        r"\band\s+([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,4})\s*,\s*(?:Freelancer|Consultant|Contractor)\b"
    ),
]
DESIGNATION_RE = re.compile(
    r"(?:designation\s+(?:will\s+be|is)|role\s+(?:will\s+be|is)|as\s+a\s+Freelancer\s*/)\s*[:\-]?\s*([A-Za-z][A-Za-z /&-]{1,80})",
    re.IGNORECASE,
)
LOCATION_RE = re.compile(r"\b(?:made|executed|entered into)[^.\n]*\b(?:at|in)\s+([A-Z][A-Za-z ]{2,40})", re.IGNORECASE)
REPAIR_TENANCY_INDICATORS = {
    "tenant",
    "landlord",
    "rent",
    "security deposit",
    "repair bill",
    "maintenance",
    "property damage",
    "move-in",
    "move-out",
    "premises condition",
}
REPAIR_NEGATIVE_CONTEXT = {
    "irreparable harm",
    "monetary damages",
    "damages would not be adequate",
    "injunctive relief",
    "breach of agreement",
    "indemnity",
    "intellectual property",
    "confidentiality",
    "representations and warranties",
}


def _normalize_value(raw: str, clause_name: str | None = None) -> str:
    lowered = raw.lower()
    if clause_name == "invoice_clause" and "monthly billing" in lowered and "7 days prior" in lowered:
        return "monthly billing invoice generated 7 days prior to month end"
    if clause_name == "payment_timing_clause" and "last week" in lowered:
        if "pro-rata" in lowered or "pro rata" in lowered:
            return "last week of the pro-rata month"
        return "last week of the month"
    if clause_name == "tds_clause":
        return "TDS deduction as applicable"
    if clause_name == "independent_contractor_clause":
        return "independent contractor relationship"
    if clause_name == "termination_notice_clause":
        duration = re.search(r"\bone\s+month(?:'s|s)?\s+written\s+notice\b", raw, re.IGNORECASE)
        if duration:
            return "one month's written notice"
    amount = AMOUNT_RE.search(raw)
    if amount:
        return amount.group(0)
    duration = re.search(r"\b\d+\s*(?:day|days|month|months|year|years)\b", raw, re.IGNORECASE)
    if duration:
        return duration.group(0)
    return raw.strip()[:120]


def _normalize_clause_key(text: str) -> str:
    lowered = text.lower().translate(str.maketrans("", "", string.punctuation))
    return " ".join(lowered.split())


def _is_valid_repairs_clause(raw: str, document_type: str) -> bool:
    lowered = raw.lower()
    if any(term in lowered for term in REPAIR_NEGATIVE_CONTEXT):
        return False
    if document_type == "tenancy_document":
        return True
    return any(term in lowered for term in REPAIR_TENANCY_INDICATORS)


def _extract_amounts(text: str) -> list[str]:
    amounts: set[str] = set()
    for match in AMOUNT_RE.finditer(text):
        value = match.group(0).strip()
        if value and not BROKEN_AMOUNT_RE.match(value):
            amounts.add(value)
    for context_match in BARE_AMOUNT_CONTEXT_RE.finditer(text):
        for number_match in BARE_NUMBER_RE.finditer(context_match.group(0)):
            value = number_match.group(0).strip()
            if value and not BROKEN_AMOUNT_RE.match(value):
                amounts.add(value)
    return sorted(amounts)


def _clean_party_name(value: str) -> str:
    cleaned = " ".join(value.replace("\u00a0", " ").split())
    cleaned = re.sub(r"\s+(?:a|an|the)\s+(?:limited liability partnership|private limited company).*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" ,.;:-")


def _title_name(value: str) -> str:
    return " ".join(part[:1].upper() + part[1:] for part in value.split())


def _looks_like_party_name(value: str) -> bool:
    lowered = value.lower()
    if any(
        phrase in lowered
        for phrase in [
            "this agreement",
            "agreement will",
            "shall",
            "will always",
            "construed",
            "clause",
            "terms",
            "conditions",
        ]
    ):
        return False
    return 1 <= len(value.split()) <= 10


def _extract_structured_facts(text: str, document_type: str) -> tuple[dict[str, str], list[str]]:
    facts: dict[str, str] = {}
    if document_type != "freelance_service_agreement":
        return facts, []

    company_match = COMPANY_RE.search(text)
    if company_match:
        facts["company_or_client"] = _clean_party_name(company_match.group(1)).upper()

    for pattern in FREELANCER_NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            facts["freelancer_name"] = _title_name(_clean_party_name(match.group(1)))
            break

    designation_match = DESIGNATION_RE.search(text)
    if designation_match:
        designation = re.split(r"\.|\n", designation_match.group(1))[0]
        facts["role_or_designation"] = " ".join(designation.split()).strip(" ,.;:-")

    date_match = DATE_RE.search(text)
    if date_match:
        facts["agreement_date"] = date_match.group(0)

    location_match = LOCATION_RE.search(text)
    if location_match:
        location = re.split(r"\s+on\b|\s+between\b|,|\.", location_match.group(1), maxsplit=1, flags=re.IGNORECASE)[0]
        facts["agreement_location"] = _title_name(" ".join(location.split()).strip(" ,.;:-"))

    parties = [
        value
        for value in [facts.get("company_or_client"), facts.get("freelancer_name")]
        if value
    ]
    return facts, parties


def _inferred_context(facts: dict[str, str], document_type: str) -> dict[str, InferredContextValue]:
    inferred: dict[str, InferredContextValue] = {}
    if facts.get("company_or_client"):
        inferred["counterparty"] = InferredContextValue(
            value=facts["company_or_client"],
            source="document party extraction",
        )
    if document_type == "freelance_service_agreement":
        inferred["user_role"] = InferredContextValue(
            value="freelancer",
            source="document type",
        )
    if facts.get("agreement_location"):
        city = facts["agreement_location"]
        inferred["city"] = InferredContextValue(value=city, source="agreement location")
        state = CITY_TO_STATE.get(city.lower())
        if state:
            inferred["state"] = InferredContextValue(value=state, source="agreement location")
    return inferred


def _dedupe_clauses(clauses: list[ExtractedClause]) -> list[ExtractedClause]:
    grouped: dict[tuple[str, int | None], ExtractedClause] = {}
    normalized_by_group: dict[tuple[str, int | None], list[str]] = {}
    for clause in clauses:
        key = (clause.name, clause.page)
        normalized = _normalize_clause_key(clause.raw_text)
        existing_norms = normalized_by_group.setdefault(key, [])
        existing = grouped.get(key)
        if existing is None:
            grouped[key] = clause
            existing_norms.append(normalized)
            continue
        existing_normalized = _normalize_clause_key(existing.raw_text)
        similar = any(
            normalized == item or normalized in item or item in normalized for item in existing_norms
        )
        if len(clause.raw_text) > len(existing.raw_text):
            clause.additional_occurrences = [existing.raw_text, *existing.additional_occurrences]
            grouped[key] = clause
        elif similar:
            existing.additional_occurrences.append(clause.raw_text)
        else:
            existing.additional_occurrences.append(clause.raw_text)
        existing_norms.append(normalized)
        existing_norms.append(existing_normalized)
    return list(grouped.values())


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
                    value=_normalize_value(raw, pattern.name),
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
        patterns = EMPLOYMENT_PATTERNS + CONTRACT_PAYMENT_PATTERNS
    elif domain == "tenancy":
        patterns = TENANCY_PATTERNS
    elif domain == "contract_payment":
        patterns = CONTRACT_PAYMENT_PATTERNS + EMPLOYMENT_PATTERNS
    clauses = _extract_patterns(text, patterns, page_texts)
    clauses = [
        clause
        for clause in clauses
        if clause.name != "repairs_maintenance" or _is_valid_repairs_clause(clause.raw_text, document_type)
    ]
    clauses = _dedupe_clauses(clauses)

    dates = sorted(set(DATE_RE.findall(text)))
    amounts = _extract_amounts(text)
    structured_facts, parties = _extract_structured_facts(text, document_type)
    party_match = PARTY_RE.search(text)
    if party_match and not parties:
        candidates = [
            " ".join(party_match.group(1).split()),
            " ".join(party_match.group(2).split()),
        ]
        if all(_looks_like_party_name(candidate) for candidate in candidates):
            parties = candidates
    inferred_context = _inferred_context(structured_facts, document_type)

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
        structured_facts=structured_facts,
        inferred_context=inferred_context,
        dates=dates,
        amounts=amounts,
        detected_domain=domain,  # type: ignore[arg-type]
        missing_fields=missing_fields,
        parser_warnings=parser_warnings or [],
    )
