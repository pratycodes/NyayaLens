from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.app.agents.human_review import evaluate_human_review
from backend.app.config import get_settings
from backend.app.core.display import display_label
from backend.app.core.schemas import FinalReport, PotentialProvisionMatch, model_to_dict
from backend.app.explainability.key_facts import key_fact_clauses
from backend.app.law_packs.coverage import (
    BSA_MISSING_WARNING,
    LawPackCoverage,
    build_law_pack_coverage,
)
from backend.app.law_packs.law_pack_loader import law_pack_status

GENERAL_INFO_LABEL = "General information from deterministic checks."

CLAUSE_LABELS = {
    "consideration_clause": "Payment/consideration clause",
    "invoice_clause": "Invoice timing",
    "payment_timing_clause": "Payment timing",
    "compensation_clause": "Compensation details",
    "pro_rata_compensation_clause": "Pro-rata compensation",
    "tds_clause": "TDS/deduction clause",
    "independent_contractor_clause": "Independent contractor relationship",
    "termination_notice_clause": "Termination notice period",
    "arbitration_clause": "Arbitration clause",
    "jurisdiction_clause": "Jurisdiction clause",
}

CLAUSE_CATEGORIES = {
    "consideration_clause": "Payment",
    "invoice_clause": "Payment",
    "payment_timing_clause": "Payment",
    "compensation_clause": "Compensation",
    "pro_rata_compensation_clause": "Compensation",
    "tds_clause": "TDS / deduction",
    "independent_contractor_clause": "Relationship",
    "termination_notice_clause": "Termination",
    "arbitration_clause": "Arbitration",
    "jurisdiction_clause": "Jurisdiction",
}

WHY_IT_MATTERS = {
    "Agreement type": "Sets the contract context for routing and remedies.",
    "Company/client": "Identifies the counterparty for written clarification.",
    "Freelancer name/role": "Worker category and role can affect practical remedy routes.",
    "Agreement date": "Helps place payment and termination duties on a timeline.",
    "Payment/consideration clause": "Anchors what payment terms the parties recorded.",
    "Invoice timing": "Helps identify when payment paperwork should have been raised.",
    "Payment timing": "Helps identify when payment may have become due.",
    "Compensation details": "Supports comparing claimed unpaid amount with the agreement.",
    "Pro-rata compensation": "May affect partial-month or partial-work calculations.",
    "TDS/deduction clause": "Separates tax deduction from disputed withholding or adjustment.",
    "Independent contractor relationship": "Can affect whether the route is contract, civil, labour, or legal-aid oriented.",
    "Termination notice period": "Can affect final payment and notice-period facts.",
    "Arbitration clause": "May affect the dispute-resolution path.",
    "Jurisdiction clause": "May affect where a dispute is raised.",
}

FREELANCE_OVERVIEW_CLAUSES = [
    "consideration_clause",
    "invoice_clause",
    "payment_timing_clause",
    "compensation_clause",
    "tds_clause",
    "jurisdiction_clause",
]

EVIDENCE_LABEL_REPLACEMENTS = [
    "contract_payment_review",
    "unpaid_compensation",
    "freelance_service_agreement",
    "contract_payment",
    "deposit_deduction",
    "repair_dispute",
    "unsafe_request",
    "employment_exit",
    "bond_recovery",
    "notice_period",
    "full_and_final",
]

SECTION_ORDER = {
    "agreement_parties": 1,
    "consideration_clause": 2,
    "invoice_clause": 3,
    "payment_timing_clause": 4,
    "compensation_clause": 5,
    "pro_rata_compensation_clause": 5,
    "tds_clause": 6,
    "independent_contractor_clause": 7,
    "termination_notice_clause": 8,
    "arbitration_clause": 9,
    "jurisdiction_clause": 10,
}


class SummaryCard(BaseModel):
    label: str
    value: str
    raw_value: str | None = None


class DocumentCitation(BaseModel):
    citation_id: str
    source_type: Literal["uploaded_document", "legal_corpus"] = "uploaded_document"
    title: str
    page: int | None = None
    section_label: str | None = None
    quote: str
    clause_id: str | None = None
    risk_ids: list[str] = Field(default_factory=list)
    fact_ids: list[str] = Field(default_factory=list)
    bbox: list[float] | None = None
    confidence: str = "medium"


class LegalCorpusCitation(BaseModel):
    citation_id: str
    source_type: Literal["legal_corpus"] = "legal_corpus"
    title: str
    domain: str | None = None
    jurisdiction: str | None = None
    source_file: str
    quote: str
    quote_preview: str
    chunk_id: str | None = None
    used_for: list[str] = Field(default_factory=list)
    corpus_mode: str = "demo"


class KeyFactRow(BaseModel):
    fact_id: str
    fact: str
    value: str
    source: str
    source_label: str
    confidence: str
    why_it_matters: str
    citation_id: str | None = None
    document_citation_ids: list[str] = Field(default_factory=list)
    legal_citation_ids: list[str] = Field(default_factory=list)


class RiskTableRow(BaseModel):
    risk_id: str
    severity: str
    title: str
    risk: str
    confidence: str
    why_it_matters: str
    evidence: str
    next_step: str
    citation_label: str
    document_citation_ids: list[str] = Field(default_factory=list)
    legal_citation_ids: list[str] = Field(default_factory=list)
    citation_labels: list[str] = Field(default_factory=list)
    general_info_label: str | None = None


class LawCrossReferenceRow(BaseModel):
    match_id: str
    legal_area: str
    potential_source: str
    why_relevant: str
    matched_facts: str
    missing_facts: str
    implication_level: str
    confidence: str
    citations: str
    human_review: str


class ImportantSection(BaseModel):
    section_id: str
    title: str
    category: str
    page: int | None = None
    quote: str
    why_it_matters: str
    linked_risk_ids: list[str] = Field(default_factory=list)
    linked_fact_ids: list[str] = Field(default_factory=list)
    severity: str | None = None
    confidence: str = "medium"
    display_order: int
    citation_id: str | None = None


class CounterpartyArgument(BaseModel):
    argument: str
    evidence_needed: str
    safe_response: str
    linked_risk_id: str | None = None
    citations: list[str] = Field(default_factory=list)


class TrustPanel(BaseModel):
    confidence: str
    confidence_reasons: list[str] = Field(default_factory=list)
    uncertainty_reasons: list[str] = Field(default_factory=list)
    corpus_mode: str
    retrieval_mode: str
    privacy_mode: str
    human_review_needed: bool
    human_review_reasons: list[str] = Field(default_factory=list)
    suggested_reviewer: str
    citation_coverage: str
    safety_status: str
    hallucination_guard_status: str
    official_corpus_coverage: str
    law_packs_loaded: list[str] = Field(default_factory=list)
    law_pack_version_dates: list[str] = Field(default_factory=list)
    criminal_law_screening_basis: str = "Not triggered"
    law_pack_coverage: list[LawPackCoverage] = Field(default_factory=list)


class ReportViewModel(BaseModel):
    summary_cards: list[SummaryCard]
    key_facts_table: list[KeyFactRow]
    key_facts: list[KeyFactRow] = Field(default_factory=list)
    risks_table: list[RiskTableRow]
    risks: list[RiskTableRow] = Field(default_factory=list)
    law_cross_references: list[LawCrossReferenceRow] = Field(default_factory=list)
    action_plan: list[str]
    safe_next_steps: list[str] = Field(default_factory=list)
    evidence_checklist: list[str]
    draft_message: str | None = None
    uploaded_document_citations: list[DocumentCitation]
    legal_corpus_citations: list[LegalCorpusCitation]
    important_sections: list[ImportantSection]
    counterparty_arguments: list[CounterpartyArgument] = Field(default_factory=list)
    trust_panel: TrustPanel
    debug_payload: dict[str, Any]


def _quote_preview(value: str, limit: int = 220) -> str:
    quote = " ".join(value.split())
    return quote if len(quote) <= limit else f"{quote[: limit - 3].rstrip()}..."


def _humanize_evidence(value: str) -> str:
    output = value.replace("issue_type:", "Issue:")
    output = output.replace("plain_text_dispute_description:", "Dispute description:")
    output = output.replace("Section 999", "[unsupported legal section requested]")
    output = output.replace("NyayaLens Act", "[unsupported law name requested]")
    output = output.replace("guarantees payment", "claims guaranteed payment")
    for raw in EVIDENCE_LABEL_REPLACEMENTS:
        output = output.replace(raw, display_label(raw))
    return output


def _document_chip(page: int | None) -> str:
    return f"Document p.{page}" if page else "Document page unavailable"


def _legal_label(citation: LegalCorpusCitation) -> str:
    return f"Source: {citation.title or citation.source_file}"


def _infer_corpus_mode_from_source(source_file: str, excerpt: str = "") -> str:
    lowered = f"{source_file} {excerpt}".lower()
    if "demo corpus" in lowered or "laws/" in lowered:
        return "demo"
    if "official" in lowered or "india_code" in lowered:
        return "official"
    return "user_uploaded"


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in value.split() if len(token) >= 5}


def _relevant_legal_citation_ids(
    risk_text: str,
    legal_citations: list[LegalCorpusCitation],
) -> list[str]:
    risk_tokens = _tokens(risk_text)
    if not risk_tokens:
        return []
    matches: list[str] = []
    for citation in legal_citations:
        source_tokens = _tokens(" ".join([citation.title, citation.quote_preview]))
        if len(risk_tokens.intersection(source_tokens)) >= 2:
            matches.append(citation.citation_id)
    return matches[:2]


def _risk_ids_for_quote(report: FinalReport, quote: str) -> list[str]:
    lowered = quote.lower()
    risk_ids: list[str] = []
    for risk in report.risk_flags:
        evidence_text = " ".join(risk.triggering_evidence + risk.document_citations).lower()
        if lowered and (lowered in evidence_text or any(item.lower() in lowered for item in risk.triggering_evidence)):
            risk_ids.append(risk.id)
    return risk_ids


def _uploaded_document_citations(report: FinalReport) -> list[DocumentCitation]:
    citations: list[DocumentCitation] = []
    facts = report.extracted_facts.structured_facts
    if facts:
        quote = ", ".join(
            value
            for value in [
                facts.get("company_or_client"),
                facts.get("freelancer_name"),
                facts.get("role_or_designation"),
                facts.get("agreement_date"),
                facts.get("agreement_location"),
            ]
            if value
        )
        if quote:
            citations.append(
                DocumentCitation(
                    citation_id="doc-facts-agreement-parties",
                    title=display_label(report.extracted_facts.document_type),
                    page=1,
                    section_label="Agreement type / parties",
                    quote=quote,
                    clause_id="agreement_parties",
                    fact_ids=["agreement_parties"],
                    confidence="medium",
                )
            )

    for index, clause in enumerate(report.extracted_facts.extracted_clauses, start=1):
        if not clause.raw_text.strip():
            continue
        label = CLAUSE_LABELS.get(clause.name, display_label(clause.name))
        citations.append(
            DocumentCitation(
                citation_id=f"doc-clause-{index}",
                title=display_label(report.extracted_facts.document_type),
                page=clause.page,
                section_label=label,
                quote=_quote_preview(clause.raw_text),
                clause_id=clause.name,
                risk_ids=_risk_ids_for_quote(report, clause.raw_text),
                confidence=clause.confidence,
            )
        )
    return citations


def _legal_corpus_citations(report: FinalReport) -> list[LegalCorpusCitation]:
    rows: list[LegalCorpusCitation] = []
    seen: set[tuple[str | None, str, str]] = set()
    for index, source in enumerate(report.retrieved_sources, start=1):
        citation = source.citation
        key = (citation.title, citation.source_file, citation.excerpt[:120])
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            LegalCorpusCitation(
                citation_id=f"legal-{index}",
                title=citation.title or citation.source_file,
                domain=citation.domain,
                jurisdiction=citation.jurisdiction,
                source_file=citation.source_file,
                quote=_quote_preview(citation.excerpt),
                quote_preview=_quote_preview(citation.excerpt),
                chunk_id=citation.chunk_id,
                used_for=[report.issue_detected.issue_type],
                corpus_mode=citation.corpus_mode or _infer_corpus_mode_from_source(citation.source_file, citation.excerpt),
            )
        )
    return rows


def _find_doc_citation(citations: list[DocumentCitation], clause_id: str) -> DocumentCitation | None:
    return next((citation for citation in citations if citation.clause_id == clause_id), None)


def _fact_id(label: str) -> str:
    return "fact-" + "".join(char.lower() if char.isalnum() else "-" for char in label).strip("-")


def _key_fact_row(
    *,
    fact: str,
    value: str,
    source: str,
    confidence: str,
    why_it_matters: str,
    citation_id: str | None = None,
) -> KeyFactRow:
    citation_ids = [citation_id] if citation_id else []
    return KeyFactRow(
        fact_id=_fact_id(fact),
        fact=fact,
        value=value,
        source=source,
        source_label=source,
        confidence=confidence,
        why_it_matters=why_it_matters,
        citation_id=citation_id,
        document_citation_ids=citation_ids,
    )


def _key_facts(report: FinalReport, doc_citations: list[DocumentCitation]) -> list[KeyFactRow]:
    rows: list[KeyFactRow] = []
    facts = report.extracted_facts.structured_facts
    agreement_citation = _find_doc_citation(doc_citations, "agreement_parties")

    rows.append(
        _key_fact_row(
            fact="Agreement type",
            value=display_label(report.extracted_facts.document_type),
            source=_document_chip(agreement_citation.page if agreement_citation else 1),
            confidence="medium",
            why_it_matters=WHY_IT_MATTERS["Agreement type"],
            citation_id=agreement_citation.citation_id if agreement_citation else None,
        )
    )
    if facts.get("company_or_client"):
        rows.append(
            _key_fact_row(
                fact="Company/client",
                value=facts["company_or_client"],
                source=_document_chip(agreement_citation.page if agreement_citation else 1),
                confidence="medium",
                why_it_matters=WHY_IT_MATTERS["Company/client"],
                citation_id=agreement_citation.citation_id if agreement_citation else None,
            )
        )
    if facts.get("freelancer_name") or facts.get("role_or_designation"):
        freelancer = facts.get("freelancer_name", "Not extracted")
        role = facts.get("role_or_designation")
        rows.append(
            _key_fact_row(
                fact="Freelancer name/role",
                value=f"{freelancer}{f' / {role}' if role else ''}",
                source=_document_chip(agreement_citation.page if agreement_citation else 1),
                confidence="medium",
                why_it_matters=WHY_IT_MATTERS["Freelancer name/role"],
                citation_id=agreement_citation.citation_id if agreement_citation else None,
            )
        )
    if facts.get("agreement_date"):
        rows.append(
            _key_fact_row(
                fact="Agreement date",
                value=facts["agreement_date"],
                source=_document_chip(agreement_citation.page if agreement_citation else 1),
                confidence="medium",
                why_it_matters=WHY_IT_MATTERS["Agreement date"],
                citation_id=agreement_citation.citation_id if agreement_citation else None,
            )
        )

    clause_rows: list[KeyFactRow] = []
    for clause in key_fact_clauses(report):
        if report.extracted_facts.document_type == "freelance_service_agreement" and clause.name not in FREELANCE_OVERVIEW_CLAUSES:
            continue
        citation = _find_doc_citation(doc_citations, clause.name)
        fact = CLAUSE_LABELS.get(clause.name, display_label(clause.name))
        clause_rows.append(
            _key_fact_row(
                fact=fact,
                value=clause.value,
                source=_document_chip(clause.page),
                confidence=clause.confidence,
                why_it_matters=WHY_IT_MATTERS.get(fact, clause.risk_hint or "Relevant extracted document fact."),
                citation_id=citation.citation_id if citation else None,
            )
        )

    rows.extend(clause_rows)
    return rows[:10]


def _risk_rows(
    report: FinalReport,
    doc_citations: list[DocumentCitation],
    legal_citations: list[LegalCorpusCitation],
) -> list[RiskTableRow]:
    rows: list[RiskTableRow] = []
    for risk in report.risk_flags:
        evidence = risk.triggering_evidence or risk.document_citations or [GENERAL_INFO_LABEL]
        display_evidence = [_humanize_evidence(item) for item in evidence]
        document_citation_ids = [
            citation.citation_id
            for citation in doc_citations
            if citation.risk_ids and risk.id in citation.risk_ids
        ]
        if not document_citation_ids:
            for citation in doc_citations:
                quote = citation.quote.lower()
                if any(item.lower() in quote or quote in item.lower() for item in evidence):
                    document_citation_ids.append(citation.citation_id)
        risk_text = " ".join([risk.title, risk.explanation, " ".join(evidence)])
        legal_citation_ids = _relevant_legal_citation_ids(risk_text, legal_citations)
        labels = [
            _document_chip(next(c.page for c in doc_citations if c.citation_id == cid))
            for cid in document_citation_ids
        ]
        labels.extend(
            _legal_label(citation)
            for citation in legal_citations
            if citation.citation_id in legal_citation_ids
        )
        if not labels:
            labels.append(GENERAL_INFO_LABEL)
        general_info_label = GENERAL_INFO_LABEL if labels == [GENERAL_INFO_LABEL] else None
        rows.append(
            RiskTableRow(
                risk_id=risk.id,
                severity=risk.severity,
                title=risk.title,
                risk=risk.title,
                confidence=risk.confidence,
                why_it_matters=risk.explanation,
                evidence=_quote_preview(" | ".join(display_evidence), limit=260),
                next_step=risk.suggested_next_step,
                citation_label=", ".join(labels),
                document_citation_ids=sorted(set(document_citation_ids)),
                legal_citation_ids=legal_citation_ids,
                citation_labels=labels,
                general_info_label=general_info_label,
            )
        )
    return rows


def _important_sections(report: FinalReport, doc_citations: list[DocumentCitation]) -> list[ImportantSection]:
    sections: list[ImportantSection] = []
    agreement_citation = _find_doc_citation(doc_citations, "agreement_parties")
    if agreement_citation:
        sections.append(
            ImportantSection(
                section_id="section-agreement-parties",
                title="Agreement type / parties",
                category="Parties",
                page=agreement_citation.page,
                quote=agreement_citation.quote,
                why_it_matters=WHY_IT_MATTERS["Agreement type"],
                confidence=agreement_citation.confidence,
                display_order=SECTION_ORDER["agreement_parties"],
                citation_id=agreement_citation.citation_id,
                linked_fact_ids=["agreement_parties"],
            )
        )

    seen: set[str] = set()
    for clause in report.extracted_facts.extracted_clauses:
        if clause.name not in SECTION_ORDER or clause.name in seen:
            continue
        seen.add(clause.name)
        citation = _find_doc_citation(doc_citations, clause.name)
        title = CLAUSE_LABELS.get(clause.name, display_label(clause.name))
        sections.append(
            ImportantSection(
                section_id=f"section-{clause.name}",
                title=title,
                category=CLAUSE_CATEGORIES.get(clause.name, "Other"),
                page=clause.page,
                quote=_quote_preview(clause.raw_text),
                why_it_matters=WHY_IT_MATTERS.get(title, clause.risk_hint or "Relevant document section."),
                linked_risk_ids=citation.risk_ids if citation else [],
                linked_fact_ids=[_fact_id(title)],
                confidence=clause.confidence,
                display_order=SECTION_ORDER[clause.name],
                citation_id=citation.citation_id if citation else None,
            )
        )
    return sorted(sections, key=lambda section: (section.display_order, section.title))


def _corpus_mode(report: FinalReport) -> str:
    modes = {
        source.citation.corpus_mode
        or _infer_corpus_mode_from_source(source.citation.source_file, source.citation.excerpt)
        for source in report.retrieved_sources
    }
    modes.discard(None)
    if not modes:
        return "demo" if report.demo_corpus_notice else "unknown"
    if modes == {"demo"}:
        return "demo"
    if modes == {"official"}:
        return "official"
    if len(modes) > 1:
        return "mixed"
    return next(iter(modes))


def _privacy_mode() -> str:
    settings = get_settings()
    if settings.llm_provider.lower() == "mock" or not settings.allow_remote_llm:
        return "Local/mock"
    return "Remote LLM available with per-analysis consent"


def _summary_cards(report: FinalReport, corpus_mode: str, privacy_mode: str) -> list[SummaryCard]:
    return [
        SummaryCard(label="Issue", value=display_label(report.issue_detected.issue_type), raw_value=report.issue_detected.issue_type),
        SummaryCard(label="Domain", value=display_label(report.issue_detected.domain), raw_value=report.issue_detected.domain),
        SummaryCard(label="Document type", value=display_label(report.extracted_facts.document_type), raw_value=report.extracted_facts.document_type),
        SummaryCard(label="Confidence", value=display_label(report.confidence), raw_value=report.confidence),
        SummaryCard(label="Risk count", value=str(len(report.risk_flags))),
        SummaryCard(label="Missing facts", value=str(len(report.missing_facts))),
        SummaryCard(label="Corpus mode", value=display_label(corpus_mode), raw_value=corpus_mode),
        SummaryCard(label="Privacy mode", value=privacy_mode),
    ]


def _retrieval_mode() -> str:
    backend = get_settings().embedding_backend.lower()
    if backend == "hash":
        return "Offline hash retrieval"
    return display_label(backend)


def _citation_coverage(
    key_facts: list[KeyFactRow],
    risk_rows: list[RiskTableRow],
) -> str:
    total = len(key_facts) + len(risk_rows)
    if not total:
        return "No report rows to evaluate"
    covered = sum(
        1
        for row in key_facts
        if row.document_citation_ids or row.legal_citation_ids or row.source_label
    )
    covered += sum(
        1
        for row in risk_rows
        if row.document_citation_ids or row.legal_citation_ids or row.general_info_label
    )
    return f"{covered}/{total} report rows have document, corpus, or deterministic-general-information support"


def _law_cross_reference_rows(matches: list[PotentialProvisionMatch]) -> list[LawCrossReferenceRow]:
    rows: list[LawCrossReferenceRow] = []
    for match in matches:
        citation_labels = [
            citation.title or citation.source_file
            for citation in match.citations
        ] or [match.source_authority or "Law pack source"]
        rows.append(
            LawCrossReferenceRow(
                match_id=match.match_id,
                legal_area=display_label(match.legal_area),
                potential_source=f"{match.act_name} {match.section_number}: {match.section_title}",
                why_relevant=match.why_relevant,
                matched_facts=_quote_preview(" | ".join(match.matched_facts) or "No facts matched.", 260),
                missing_facts=", ".join(match.missing_facts[:8]) or "No missing facts listed.",
                implication_level=display_label(match.implication_level),
                confidence=display_label(match.confidence),
                citations=", ".join(citation_labels),
                human_review="Yes" if match.human_review_needed else "No",
            )
        )
    return rows


def _official_corpus_coverage(matches: list[PotentialProvisionMatch]) -> str:
    if not matches:
        return "No law-pack matches"
    modes = {match.corpus_mode for match in matches}
    if modes == {"official"}:
        return "Official law-pack matches only"
    if "official" in modes:
        return "Mixed demo/official law-pack matches"
    return "Demo law-pack matches only"


def _criminal_law_screening_basis(matches: list[PotentialProvisionMatch]) -> str:
    criminal = [match for match in matches if match.legal_area == "criminal_screening"]
    if not criminal:
        return "Not triggered"
    act_names = {match.act_name for match in criminal}
    if any("Bharatiya Nyaya Sanhita" in name for name in act_names):
        return "Current criminal screening used available BNS/BNSS/BSA law-pack markers"
    if any("Indian Penal Code" in name for name in act_names):
        return "Historical criminal screening used IPC pre-2024-07-01 marker"
    return "Criminal screening law-pack marker used"


def _trust_panel(
    report: FinalReport,
    key_facts: list[KeyFactRow],
    risk_rows: list[RiskTableRow],
    corpus_mode: str,
    privacy_mode: str,
) -> TrustPanel:
    human_review = evaluate_human_review(report)
    status = law_pack_status()
    law_pack_coverage = build_law_pack_coverage()
    confidence_reasons = [
        f"Issue confidence: {display_label(report.issue_detected.confidence)}",
        f"Jurisdiction confidence: {display_label(report.jurisdiction.confidence)}",
        "Verifier passed." if report.verifier.passed else "Verifier requested conservative handling.",
    ]
    uncertainty_reasons = list(report.uncertainties)
    if corpus_mode == "demo":
        uncertainty_reasons.append("Demo corpus is simplified and educational; official sources are not enabled.")
    for row in law_pack_coverage:
        if row.act_id == "bsa_2023" and row.status != "loaded_official":
            uncertainty_reasons.append(BSA_MISSING_WARNING)
        if row.status in {"missing_official", "rejected_metadata_mismatch"}:
            uncertainty_reasons.extend(row.warnings[:3])
    for fact in report.missing_facts[:8]:
        uncertainty_reasons.append(f"Missing fact: {fact}")
    safety = report.issue_detected.safety_result
    safety_status = (
        "Unsafe user intent refused."
        if report.issue_detected.unsafe_request
        else (safety.reason if safety else "No unsafe user intent detected.")
    )
    return TrustPanel(
        confidence=display_label(report.confidence),
        confidence_reasons=confidence_reasons,
        uncertainty_reasons=sorted(set(uncertainty_reasons)),
        corpus_mode=display_label(corpus_mode),
        retrieval_mode=_retrieval_mode(),
        privacy_mode=privacy_mode,
        human_review_needed=human_review.needed,
        human_review_reasons=human_review.reasons,
        suggested_reviewer=human_review.suggested_reviewer,
        citation_coverage=_citation_coverage(key_facts, risk_rows),
        safety_status=safety_status,
        hallucination_guard_status=(
            "Verifier requires citations, deterministic-general-information labels, and no outcome guarantees."
        ),
        official_corpus_coverage=_official_corpus_coverage(report.potential_provision_matches),
        law_packs_loaded=status.law_packs_loaded,
        law_pack_version_dates=status.version_dates,
        criminal_law_screening_basis=_criminal_law_screening_basis(report.potential_provision_matches),
        law_pack_coverage=law_pack_coverage,
    )


def _counterparty_arguments(report: FinalReport, risk_rows: list[RiskTableRow]) -> list[CounterpartyArgument]:
    issue = report.issue_detected.issue_type
    domain = report.issue_detected.domain
    risk_by_title = {row.risk.lower(): row.risk_id for row in risk_rows}
    if domain == "contract_payment" or issue in {"unpaid_compensation", "contract_payment_review"}:
        return [
            CounterpartyArgument(
                argument="Work was incomplete",
                evidence_needed="Work delivery proof, acceptance messages, task logs, and scope-of-work records.",
                safe_response="Ask for a written defect list and current payment/acceptance status.",
                linked_risk_id=next(iter(risk_by_title.values()), None),
            ),
            CounterpartyArgument(
                argument="Payment is not due yet",
                evidence_needed="Invoice date, payment timing clause, due date, and approval messages.",
                safe_response="Compare the due date with the agreement and request a written payment timeline.",
            ),
            CounterpartyArgument(
                argument="Deduction is TDS",
                evidence_needed="TDS certificate, itemized calculation, payment ledger, and deduction communication.",
                safe_response="Ask for itemized deduction details and TDS certificate/payment particulars.",
            ),
            CounterpartyArgument(
                argument="Arbitration or forum clause applies",
                evidence_needed="Arbitration and jurisdiction clauses from the agreement.",
                safe_response="Seek legal-aid or lawyer review before escalation.",
            ),
        ]
    if domain == "tenancy":
        return [
            CounterpartyArgument(
                argument="Damage was caused by tenant",
                evidence_needed="Move-in/move-out photos, inspection notes, repair bills, and messages.",
                safe_response="Ask for itemized bills and photos supporting each deduction.",
            ),
            CounterpartyArgument(
                argument="Unpaid rent or lock-in breach",
                evidence_needed="Rent receipts, payment ledger, lock-in clause, and notice records.",
                safe_response="Request a written calculation and clause reference.",
            ),
        ]
    if domain == "employment":
        return [
            CounterpartyArgument(
                argument="Bond, notice period, or FNF adjustment applies",
                evidence_needed="Offer letter, HR policy, training proof, payslips, and resignation emails.",
                safe_response="Ask HR/payroll for a written clause reference and itemized calculation.",
            ),
            CounterpartyArgument(
                argument="Confidentiality or non-compete obligations apply",
                evidence_needed="Restrictive covenant clause and any employer communication.",
                safe_response="Get legal review before accepting broad restrictions or undertakings.",
            ),
        ]
    return []


def to_report_view_model(report: FinalReport) -> ReportViewModel:
    doc_citations = _uploaded_document_citations(report)
    legal_citations = _legal_corpus_citations(report)
    key_facts = _key_facts(report, doc_citations)
    risk_rows = _risk_rows(report, doc_citations, legal_citations)
    law_rows = _law_cross_reference_rows(report.potential_provision_matches)
    corpus_mode = _corpus_mode(report)
    privacy_mode = _privacy_mode()
    trust_panel = _trust_panel(report, key_facts, risk_rows, corpus_mode, privacy_mode)
    return ReportViewModel(
        summary_cards=_summary_cards(report, corpus_mode, privacy_mode),
        key_facts_table=key_facts,
        key_facts=key_facts,
        risks_table=risk_rows,
        risks=risk_rows,
        law_cross_references=law_rows,
        action_plan=report.remedy_plan.steps,
        safe_next_steps=report.remedy_plan.steps,
        evidence_checklist=report.remedy_plan.evidence_checklist,
        draft_message=report.remedy_plan.draft_message,
        uploaded_document_citations=doc_citations,
        legal_corpus_citations=legal_citations,
        important_sections=_important_sections(report, doc_citations),
        counterparty_arguments=_counterparty_arguments(report, risk_rows),
        trust_panel=trust_panel,
        debug_payload={
            "raw_issue": model_to_dict(report.issue_detected),
            "raw_expert_route": model_to_dict(report.expert_route),
            "raw_extracted_clauses": [model_to_dict(clause) for clause in report.extracted_facts.extracted_clauses],
            "rule_checks": [model_to_dict(rule) for rule in report.rule_checks],
            "potential_provision_matches": [
                model_to_dict(match) for match in report.potential_provision_matches
            ],
            "law_pack_coverage": [model_to_dict(row) for row in trust_panel.law_pack_coverage],
            "retrieved_source_metadata": [
                {
                    **model_to_dict(source.citation),
                    "score": source.score,
                }
                for source in report.retrieved_sources
            ],
            "audit_trace": [model_to_dict(entry) for entry in report.audit_trace],
            "verifier": model_to_dict(report.verifier),
            "raw_report": model_to_dict(report),
        },
    )
