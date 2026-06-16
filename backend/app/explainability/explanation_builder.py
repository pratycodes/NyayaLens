from __future__ import annotations

from backend.app.core.constants import DEMO_CORPUS_NOTICE, LEGAL_DISCLAIMER
from backend.app.core.schemas import (
    AuditTraceEntry,
    DocumentAnalysis,
    ExpertRoute,
    FinalReport,
    IssueAnalysis,
    JurisdictionResult,
    RemedyPlan,
    RetrievedSource,
    RiskFlag,
    RuleResult,
    VerifierResult,
)
from backend.app.explainability.citations import collect_citations
from backend.app.rules.risk_scoring import overall_confidence


def missing_facts(
    document: DocumentAnalysis,
    jurisdiction: JurisdictionResult,
    issue: IssueAnalysis,
) -> list[str]:
    facts = list(document.missing_fields)
    if not jurisdiction.state:
        facts.append("state")
    if not jurisdiction.city:
        facts.append("city")
    if issue.domain == "employment":
        for field in ["user role/category", "resignation date", "salary/FNF status", "HR policy"]:
            if field not in facts:
                facts.append(field)
    elif issue.domain == "tenancy":
        for field in ["move-in/move-out condition", "itemized bills", "rent payment proof"]:
            if field not in facts:
                facts.append(field)
    return sorted(set(facts))


def uncertainties(document: DocumentAnalysis, jurisdiction: JurisdictionResult, sources: list[RetrievedSource]) -> list[str]:
    values: list[str] = []
    if jurisdiction.warnings:
        values.extend(jurisdiction.warnings)
    if any("DEMO CORPUS" in source.citation.excerpt for source in sources):
        values.append("Only demo corpus material may have been retrieved; it is not a complete statement of Indian law.")
    if document.parser_warnings:
        values.extend(document.parser_warnings)
    return sorted(set(values))


def build_final_report(
    *,
    analysis_id: str,
    issue: IssueAnalysis,
    document: DocumentAnalysis,
    route: ExpertRoute,
    jurisdiction: JurisdictionResult,
    retrieved_sources: list[RetrievedSource],
    rules: list[RuleResult],
    risks: list[RiskFlag],
    remedy: RemedyPlan,
    verifier: VerifierResult,
    audit_trace: list[AuditTraceEntry],
) -> FinalReport:
    citations = collect_citations(retrieved_sources)
    confidence = overall_confidence(
        [issue.confidence, jurisdiction.confidence, route.confidence, verifier.passed and "high" or "low"]  # type: ignore[list-item]
    )
    return FinalReport(
        analysis_id=analysis_id,
        disclaimer=LEGAL_DISCLAIMER,
        demo_corpus_notice=DEMO_CORPUS_NOTICE,
        issue_detected=issue,
        extracted_facts=document,
        missing_facts=missing_facts(document, jurisdiction, issue),
        expert_route=route,
        jurisdiction=jurisdiction,
        retrieved_sources=retrieved_sources,
        rule_checks=rules,
        risk_flags=risks,
        uncertainties=uncertainties(document, jurisdiction, retrieved_sources),
        remedy_plan=remedy,
        citations=citations,
        confidence=confidence,
        verifier=verifier,
        audit_trace=audit_trace,
    )
