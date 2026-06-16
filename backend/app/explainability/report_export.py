from __future__ import annotations

import json

from backend.app.core.schemas import FinalReport, model_to_dict
from backend.app.explainability.report_view_model import ReportViewModel


def markdown_report(report: FinalReport, view_model: ReportViewModel) -> str:
    lines = [
        "# NyayaLens Analysis Report",
        "",
        report.disclaimer,
        "",
        "## Summary",
    ]
    for card in view_model.summary_cards:
        lines.append(f"- **{card.label}:** {card.value}")
    lines.extend(["", "## Key Facts"])
    for row in view_model.key_facts:
        lines.append(f"- **{row.fact}:** {row.value} ({row.source_label})")
    lines.extend(["", "## Risks"])
    for row in view_model.risks:
        lines.append(
            f"- **{row.severity.upper()} - {row.risk}:** {row.why_it_matters} "
            f"Evidence: {row.evidence}. Citation: {row.citation_label}. Next step: {row.next_step}"
        )
    lines.extend(["", "## Potentially Implicated Provisions"])
    lines.append(
        "NyayaLens identifies potentially relevant provisions and missing facts. "
        "It does not determine that a law has been broken."
    )
    for row in view_model.law_cross_references:
        lines.append(
            f"- **{row.legal_area}:** {row.potential_source}. "
            f"Implication level: {row.implication_level}. Missing facts: {row.missing_facts}."
        )
    lines.extend(["", "## Missing Facts"])
    for fact in report.missing_facts:
        lines.append(f"- {fact}")
    lines.extend(["", "## Important Document Sections"])
    for section in view_model.important_sections:
        page = f"Document p.{section.page}" if section.page else "Document page unavailable"
        lines.append(f"- **{section.title}:** {page}. {section.why_it_matters}")
    lines.extend(["", "## Safe Next Steps"])
    for step in view_model.safe_next_steps:
        lines.append(f"- {step}")
    lines.extend(["", "## Evidence Checklist"])
    for item in view_model.evidence_checklist:
        lines.append(f"- {item}")
    if view_model.draft_message:
        lines.extend(["", "## Draft Message", "", "```text", view_model.draft_message, "```"])
    lines.extend(["", "## Citations"])
    for citation in view_model.uploaded_document_citations:
        page = f"p.{citation.page}" if citation.page else "page unavailable"
        lines.append(f"- Uploaded document {page}: {citation.quote}")
    for citation in view_model.legal_corpus_citations:
        lines.append(f"- {citation.title} ({citation.corpus_mode}): {citation.quote_preview}")
    lines.extend(["", "## Trust Notes"])
    lines.append(f"- Confidence: {view_model.trust_panel.confidence}")
    lines.append(f"- Citation coverage: {view_model.trust_panel.citation_coverage}")
    for reason in view_model.trust_panel.uncertainty_reasons:
        lines.append(f"- {reason}")
    return "\n".join(lines)


def json_report(view_model: ReportViewModel) -> str:
    payload = view_model.model_dump(mode="json")
    payload.pop("debug_payload", None)
    return json.dumps(payload, indent=2, ensure_ascii=False)


def raw_json_report(report: FinalReport) -> str:
    return json.dumps(model_to_dict(report), indent=2, ensure_ascii=False)
