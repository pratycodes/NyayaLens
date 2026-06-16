from __future__ import annotations

import uuid

from backend.app.agents.expert_router import route_expert
from backend.app.agents.issue_spotter import spot_issue
from backend.app.agents.jurisdiction_router import route_jurisdiction
from backend.app.agents.remedy_planner import plan_remedy
from backend.app.agents.state import AnalysisState
from backend.app.agents.verifier_agent import verify_report_parts
from backend.app.core.constants import LEGAL_DISCLAIMER
from backend.app.core.schemas import (
    FinalReport,
    UploadMetadata,
    UserContext,
)
from backend.app.documents.clause_extractor import extract_document_analysis
from backend.app.explainability.audit_trace import trace
from backend.app.explainability.citations import collect_citations
from backend.app.explainability.explanation_builder import build_final_report
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.rules.engine import apply_rules
from backend.app.storage.sqlite import save_analysis


def _audit(state: AnalysisState, node: str, input_summary: str, output_summary: str, warnings: list[str] | None = None) -> None:
    state.setdefault("audit_trace", []).append(trace(node, input_summary, output_summary, warnings))


def parse_document_node(state: AnalysisState) -> AnalysisState:
    # Text parsing happens before this node for API uploads; this node records metadata for traceability.
    text = state.get("document_text", "")
    metadata = state.get("upload_metadata", UploadMetadata())
    _audit(
        state,
        "parse_document",
        f"{metadata.filename}, {len(text)} chars",
        "Document text available for extraction.",
        state.get("parser_warnings", []),
    )
    return state


def extract_clauses_node(state: AnalysisState) -> AnalysisState:
    document = extract_document_analysis(
        state.get("document_text", ""),
        page_texts=state.get("page_texts"),
        parser_warnings=state.get("parser_warnings", []),
    )
    state["document_analysis"] = document
    _audit(
        state,
        "extract_clauses",
        f"{len(state.get('document_text', ''))} chars",
        f"{len(document.extracted_clauses)} clauses, domain={document.detected_domain}",
        document.parser_warnings,
    )
    return state


def spot_issue_node(state: AnalysisState) -> AnalysisState:
    issue = spot_issue(
        state.get("document_text", ""),
        state["document_analysis"],
        state.get("user_context", UserContext()),
    )
    state["issue_analysis"] = issue
    _audit(
        state,
        "spot_issue",
        state["document_analysis"].detected_domain,
        f"{issue.domain}:{issue.issue_type} ({issue.confidence})",
        [issue.refusal_message] if issue.refusal_message else [],
    )
    return state


def route_jurisdiction_node(state: AnalysisState) -> AnalysisState:
    jurisdiction = route_jurisdiction(
        state.get("document_text", ""),
        state["document_analysis"],
        state.get("user_context", UserContext()),
    )
    state["jurisdiction"] = jurisdiction
    _audit(
        state,
        "route_jurisdiction",
        "context + document text",
        f"state={jurisdiction.state}, city={jurisdiction.city}, confidence={jurisdiction.confidence}",
        jurisdiction.warnings,
    )
    return state


def route_expert_node(state: AnalysisState) -> AnalysisState:
    route = route_expert(state["issue_analysis"])
    state["expert_route"] = route
    _audit(
        state,
        "route_expert",
        state["issue_analysis"].issue_type,
        f"primary={route.primary_expert}, secondary={', '.join(route.secondary_experts)}",
    )
    return state


def retrieve_sources_node(state: AnalysisState) -> AnalysisState:
    issue = state["issue_analysis"]
    context = state.get("user_context", UserContext())
    query = " ".join(
        [
            issue.domain,
            issue.issue_type,
            context.query or "",
            " ".join(clause.raw_text for clause in state["document_analysis"].extracted_clauses[:8]),
        ]
    )
    sources = HybridRetriever().retrieve(query, domain=issue.domain, k=5)
    state["retrieved_sources"] = sources
    _audit(
        state,
        "retrieve_sources",
        f"query domain={issue.domain}",
        f"{len(sources)} sources retrieved",
        ["No local corpus sources retrieved."] if not sources else [],
    )
    return state


def apply_rules_node(state: AnalysisState) -> AnalysisState:
    citations = collect_citations(state.get("retrieved_sources", []))
    rules, risks = apply_rules(
        document=state["document_analysis"],
        issue=state["issue_analysis"],
        context=state.get("user_context", UserContext()),
        jurisdiction=state["jurisdiction"],
        source_citations=citations,
    )
    state["rule_results"] = rules
    state["risk_flags"] = risks
    _audit(
        state,
        "apply_rules",
        f"{state['issue_analysis'].issue_type}",
        f"{len(rules)} rules, {len(risks)} risk flags",
    )
    return state


def build_explanation_node(state: AnalysisState) -> AnalysisState:
    _audit(
        state,
        "build_explanation",
        "rules + retrieval + clauses",
        "Report sections prepared before verification.",
    )
    return state


def verify_answer_node(state: AnalysisState) -> AnalysisState:
    citations = collect_citations(state.get("retrieved_sources", []))
    verifier = verify_report_parts(
        disclaimer=LEGAL_DISCLAIMER,
        issue=state["issue_analysis"],
        jurisdiction=state["jurisdiction"],
        rules=state["rule_results"],
        risks=state["risk_flags"],
        remedy=state.get("remedy_plan") or plan_remedy(
            state["issue_analysis"], state["risk_flags"], state.get("user_context", UserContext())
        ),
        citations=citations,
    )
    state["verifier_result"] = verifier
    _audit(
        state,
        "verify_answer",
        f"{len(citations)} citations",
        "passed" if verifier.passed else "failed",
        verifier.warnings,
    )
    return state


def plan_remedy_node(state: AnalysisState) -> AnalysisState:
    remedy = plan_remedy(
        state["issue_analysis"],
        state.get("risk_flags", []),
        state.get("user_context", UserContext()),
    )
    state["remedy_plan"] = remedy
    _audit(
        state,
        "plan_remedy",
        state["issue_analysis"].issue_type,
        f"{len(remedy.steps)} steps, {len(remedy.evidence_checklist)} evidence items",
    )
    return state


def safety_finalize_node(state: AnalysisState) -> AnalysisState:
    # Run verifier once more after remedy is finalized.
    citations = collect_citations(state.get("retrieved_sources", []))
    verifier = verify_report_parts(
        disclaimer=LEGAL_DISCLAIMER,
        issue=state["issue_analysis"],
        jurisdiction=state["jurisdiction"],
        rules=state["rule_results"],
        risks=state["risk_flags"],
        remedy=state["remedy_plan"],
        citations=citations,
    )
    state["verifier_result"] = verifier
    report = build_final_report(
        analysis_id=state["analysis_id"],
        issue=state["issue_analysis"],
        document=state["document_analysis"],
        route=state["expert_route"],
        jurisdiction=state["jurisdiction"],
        retrieved_sources=state.get("retrieved_sources", []),
        rules=state.get("rule_results", []),
        risks=state.get("risk_flags", []),
        remedy=state["remedy_plan"],
        verifier=verifier,
        audit_trace=state.get("audit_trace", []),
    )
    state["final_report"] = report
    _audit(
        state,
        "safety_finalize",
        "verified parts",
        f"final confidence={report.confidence}",
        verifier.warnings,
    )
    # Rebuild once to include the safety_finalize trace entry.
    state["final_report"] = build_final_report(
        analysis_id=state["analysis_id"],
        issue=state["issue_analysis"],
        document=state["document_analysis"],
        route=state["expert_route"],
        jurisdiction=state["jurisdiction"],
        retrieved_sources=state.get("retrieved_sources", []),
        rules=state.get("rule_results", []),
        risks=state.get("risk_flags", []),
        remedy=state["remedy_plan"],
        verifier=verifier,
        audit_trace=state.get("audit_trace", []),
    )
    return state


NODE_SEQUENCE = [
    parse_document_node,
    extract_clauses_node,
    spot_issue_node,
    route_jurisdiction_node,
    route_expert_node,
    retrieve_sources_node,
    apply_rules_node,
    build_explanation_node,
    plan_remedy_node,
    verify_answer_node,
    safety_finalize_node,
]


def build_langgraph_app():
    """Build the LangGraph state machine when langgraph is installed."""
    try:
        from langgraph.graph import END, StateGraph  # type: ignore
    except Exception:
        return None

    graph = StateGraph(AnalysisState)
    graph.add_node("parse_document", parse_document_node)
    graph.add_node("extract_clauses", extract_clauses_node)
    graph.add_node("spot_issue", spot_issue_node)
    graph.add_node("route_jurisdiction", route_jurisdiction_node)
    graph.add_node("route_expert", route_expert_node)
    graph.add_node("retrieve_sources", retrieve_sources_node)
    graph.add_node("apply_rules", apply_rules_node)
    graph.add_node("build_explanation", build_explanation_node)
    graph.add_node("plan_remedy", plan_remedy_node)
    graph.add_node("verify_answer", verify_answer_node)
    graph.add_node("safety_finalize", safety_finalize_node)

    graph.set_entry_point("parse_document")
    graph.add_edge("parse_document", "extract_clauses")
    graph.add_edge("extract_clauses", "spot_issue")
    graph.add_edge("spot_issue", "route_jurisdiction")
    graph.add_edge("route_jurisdiction", "route_expert")
    graph.add_edge("route_expert", "retrieve_sources")
    graph.add_edge("retrieve_sources", "apply_rules")
    graph.add_edge("apply_rules", "build_explanation")
    graph.add_edge("build_explanation", "plan_remedy")
    graph.add_edge("plan_remedy", "verify_answer")
    graph.add_edge("verify_answer", "safety_finalize")
    graph.add_edge("safety_finalize", END)
    return graph.compile()


def run_analysis(
    *,
    text: str,
    context: UserContext | None = None,
    filename: str = "plain_text.txt",
    page_texts: list[tuple[int, str]] | None = None,
    parser_warnings: list[str] | None = None,
    upload_id: str | None = None,
    persist: bool = True,
    use_langgraph: bool = False,
) -> FinalReport:
    state: AnalysisState = {
        "analysis_id": str(uuid.uuid4()),
        "upload_metadata": UploadMetadata(
            filename=filename,
            content_type="text/plain",
            size_bytes=len(text.encode("utf-8")),
            upload_id=upload_id,
        ),
        "document_text": text,
        "page_texts": page_texts or [(1, text)],
        "parser_warnings": parser_warnings or [],
        "user_context": context or UserContext(),
        "audit_trace": [],
    }
    app = build_langgraph_app() if use_langgraph else None
    if app is not None:
        state = app.invoke(state)
    else:
        for node in NODE_SEQUENCE:
            state = node(state)
    report = state["final_report"]
    if persist:
        save_analysis(report, upload_id=upload_id, filename=filename)
    return report
