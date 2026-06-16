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


class DocumentAnalysis(BaseModel):
    document_type: str
    extracted_clauses: list[ExtractedClause] = Field(default_factory=list)
    parties: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    detected_domain: Literal["employment", "tenancy", "unknown"] = "unknown"
    missing_fields: list[str] = Field(default_factory=list)
    parser_warnings: list[str] = Field(default_factory=list)


class IssueAnalysis(BaseModel):
    domain: Literal["employment", "tenancy", "unknown"] = "unknown"
    issue_type: str = "unknown"
    confidence: Confidence = "low"
    reasons: list[str] = Field(default_factory=list)
    unsafe_request: bool = False
    refusal_message: str | None = None


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
    node_name: str
    input_summary: str
    output_summary: str
    warnings: list[str] = Field(default_factory=list)
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
