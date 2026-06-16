from __future__ import annotations

from typing import Any, TypedDict

from backend.app.core.schemas import (
    AuditTraceEntry,
    DocumentAnalysis,
    ExpertRoute,
    FinalReport,
    IssueAnalysis,
    JurisdictionResult,
    PotentialProvisionMatch,
    RemedyPlan,
    RetrievedSource,
    RiskFlag,
    RuleResult,
    UploadMetadata,
    UserContext,
    VerifierResult,
)


class AnalysisState(TypedDict, total=False):
    analysis_id: str
    upload_metadata: UploadMetadata
    document_text: str
    page_texts: list[tuple[int, str]]
    parser_warnings: list[str]
    user_context: UserContext
    document_analysis: DocumentAnalysis
    issue_analysis: IssueAnalysis
    jurisdiction: JurisdictionResult
    expert_route: ExpertRoute
    retrieved_sources: list[RetrievedSource]
    potential_provision_matches: list[PotentialProvisionMatch]
    rule_results: list[RuleResult]
    risk_flags: list[RiskFlag]
    remedy_plan: RemedyPlan
    verifier_result: VerifierResult
    final_report: FinalReport
    audit_trace: list[AuditTraceEntry]
    extra: dict[str, Any]
