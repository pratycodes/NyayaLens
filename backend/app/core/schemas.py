from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high"]
Confidence = Literal["low", "medium", "high"]


class UserContext(BaseModel):
    state: str | None = None
    city: str | None = None
    user_role: str | None = None
    counterparty: str | None = None
    dispute_date: str | None = None
    urgency: str | None = None
    selected_dispute_type: str | None = "auto-detect"
    query: str | None = None
    allow_remote_llm: bool = False


class UploadMetadata(BaseModel):
    filename: str = "plain_text.txt"
    content_type: str | None = "text/plain"
    size_bytes: int | None = None
    upload_id: str | None = None


class ExtractedClause(BaseModel):
    name: str
    value: str
    raw_text: str
    page: int | None = None
    confidence: Confidence = "medium"
    risk_hint: str | None = None
    additional_occurrences: list[str] = Field(default_factory=list)


class InferredContextValue(BaseModel):
    value: str
    source: str


class DocumentAnalysis(BaseModel):
    document_type: str
    extracted_clauses: list[ExtractedClause] = Field(default_factory=list)
    parties: list[str] = Field(default_factory=list)
    structured_facts: dict[str, str] = Field(default_factory=dict)
    inferred_context: dict[str, InferredContextValue] = Field(default_factory=dict)
    dates: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    detected_domain: Literal["employment", "tenancy", "contract_payment", "unknown"] = "unknown"
    missing_fields: list[str] = Field(default_factory=list)
    parser_warnings: list[str] = Field(default_factory=list)


class SafetyResult(BaseModel):
    is_unsafe_intent: bool = False
    matched_terms: list[str] = Field(default_factory=list)
    matched_patterns: list[str] = Field(default_factory=list)
    scope: Literal["user_intent_only"] = "user_intent_only"
    reason: str = "No unsafe user intent detected."


class IssueAnalysis(BaseModel):
    domain: Literal["employment", "tenancy", "contract_payment", "safety", "unknown"] = "unknown"
    issue_type: str = "unknown"
    confidence: Confidence = "low"
    reasons: list[str] = Field(default_factory=list)
    unsafe_request: bool = False
    refusal_message: str | None = None
    safety_result: SafetyResult | None = None


class JurisdictionResult(BaseModel):
    state: str | None = None
    city: str | None = None
    jurisdiction_clause: str | None = None
    confidence: Confidence = "low"
    warnings: list[str] = Field(default_factory=list)


class ExpertRoute(BaseModel):
    primary_expert: str
    secondary_experts: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"
    route_reason: str


class Citation(BaseModel):
    source_file: str
    title: str | None = None
    domain: str | None = None
    jurisdiction: str | None = None
    page: int | None = None
    chunk_id: str | None = None
    excerpt: str
    corpus_mode: str | None = None


class RetrievedSource(BaseModel):
    citation: Citation
    score: float


class RuleResult(BaseModel):
    id: str
    passed: bool
    title: str
    severity: Severity = "low"
    confidence: Confidence = "medium"
    evidence: list[str] = Field(default_factory=list)
    explanation: str
    suggested_next_step: str | None = None


class RiskFlag(BaseModel):
    id: str
    title: str
    severity: Severity
    confidence: Confidence
    triggering_evidence: list[str] = Field(default_factory=list)
    explanation: str
    suggested_next_step: str
    source_citations: list[Citation] = Field(default_factory=list)
    document_citations: list[str] = Field(default_factory=list)


class PotentialProvisionMatch(BaseModel):
    match_id: str
    legal_area: str
    act_name: str
    section_number: str
    section_title: str
    source_quote: str
    why_relevant: str
    matched_facts: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"
    implication_level: Literal[
        "relevant_provision_found",
        "possible_civil_breach",
        "possible_statutory_non_compliance",
        "possible_criminal_allegation",
        "not_enough_facts",
    ] = "relevant_provision_found"
    human_review_needed: bool = False
    citations: list[Citation] = Field(default_factory=list)
    corpus_mode: str = "demo"
    effective_from: str | None = None
    effective_to: str | None = None
    version_date: str | None = None
    source_authority: str | None = None
    source_url: str | None = None


class RemedyPlan(BaseModel):
    steps: list[str] = Field(default_factory=list)
    evidence_checklist: list[str] = Field(default_factory=list)
    draft_message: str | None = None
    escalation_note: str | None = None


class VerifierResult(BaseModel):
    passed: bool
    warnings: list[str] = Field(default_factory=list)
    conservative_message: str | None = None


class AuditTraceEntry(BaseModel):
    analysis_id: str | None = None
    node_name: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    input_summary: str
    output_summary: str
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FinalReport(BaseModel):
    analysis_id: str
    disclaimer: str
    demo_corpus_notice: str
    issue_detected: IssueAnalysis
    extracted_facts: DocumentAnalysis
    missing_facts: list[str]
    expert_route: ExpertRoute
    jurisdiction: JurisdictionResult
    retrieved_sources: list[RetrievedSource]
    rule_checks: list[RuleResult]
    risk_flags: list[RiskFlag]
    potential_provision_matches: list[PotentialProvisionMatch] = Field(default_factory=list)
    uncertainties: list[str]
    remedy_plan: RemedyPlan
    citations: list[Citation]
    confidence: Confidence
    verifier: VerifierResult
    audit_trace: list[AuditTraceEntry]
    safe_followup_enabled: bool = True


class AnalyzeRequest(BaseModel):
    text: str | None = None
    upload_id: str | None = None
    filename: str = "plain_text.txt"
    context: UserContext = Field(default_factory=UserContext)


class AnalyzeResponse(BaseModel):
    report: FinalReport


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    parser_warnings: list[str] = Field(default_factory=list)


class CorpusStatus(BaseModel):
    chunk_count: int
    source_files: list[str]
    using_demo_corpus: bool
    persist_dir: str


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()
