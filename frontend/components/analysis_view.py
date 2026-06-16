from __future__ import annotations

import json

import streamlit as st
from backend.app.config import get_settings
from backend.app.core.display import display_label
from backend.app.core.schemas import FinalReport, model_to_dict
from backend.app.explainability.report_export import json_report, markdown_report, raw_json_report
from backend.app.explainability.report_view_model import ReportViewModel, to_report_view_model

from frontend.components.pdf_viewer import render_document_viewer


def _select_document_citation(citation_id: str, page: int | None) -> None:
    st.session_state["nl_selected_document_citation_id"] = citation_id
    st.session_state["nl_selected_page"] = page or 1


def _render_summary_cards(view_model: ReportViewModel) -> None:
    for start in range(0, len(view_model.summary_cards), 4):
        columns = st.columns(4)
        for column, card in zip(columns, view_model.summary_cards[start : start + 4], strict=False):
            with column.container(border=True):
                st.caption(card.label)
                st.write(card.value)


def _render_overview(report: FinalReport, view_model: ReportViewModel) -> None:
    _render_summary_cards(view_model)
    st.subheader("Key Facts")
    st.dataframe(
        [
            {
                "Fact": row.fact,
                "Value": row.value,
                "Source": row.source_label,
                "Confidence": display_label(row.confidence),
                "Why it matters": row.why_it_matters,
            }
            for row in view_model.key_facts_table
        ],
        hide_index=True,
        use_container_width=True,
    )


def _filtered_risks(view_model: ReportViewModel) -> list:
    severity = st.radio("Severity", ["all", "high", "medium", "low"], horizontal=True)
    only_document = st.checkbox("Show only risks with document citations")
    search = st.text_input("Search risk text")
    rows = view_model.risks_table
    if severity != "all":
        rows = [row for row in rows if row.severity == severity]
    if only_document:
        rows = [row for row in rows if row.document_citation_ids]
    if search.strip():
        needle = search.lower()
        rows = [
            row
            for row in rows
            if needle
            in " ".join([row.risk, row.why_it_matters, row.evidence, row.next_step]).lower()
        ]
    return rows


def _render_risks(view_model: ReportViewModel) -> None:
    st.subheader("Risk Flags")
    rows = _filtered_risks(view_model)
    if not rows:
        st.info("No risks match the current filters.")
        return

    table = [
        {
            "Severity": row.severity.upper(),
            "Risk": row.risk,
            "Confidence": display_label(row.confidence),
            "Why it matters": row.why_it_matters,
            "Evidence": row.evidence,
            "Next step": row.next_step,
            "Citation": row.citation_label,
        }
        for row in rows
    ]
    st.dataframe(table, hide_index=True, use_container_width=True)

    st.markdown("**View Risk Evidence**")
    for row in rows:
        if not row.document_citation_ids:
            continue
        with st.container(border=True):
            st.write(f"**{row.risk}**")
            st.caption(", ".join(row.citation_labels))
            citation_id = row.document_citation_ids[0]
            citation = next(
                item
                for item in view_model.uploaded_document_citations
                if item.citation_id == citation_id
            )
            if st.button("View in document", key=f"risk-view-{row.risk_id}"):
                _select_document_citation(citation_id, citation.page)
                st.session_state["nl_document_view_message"] = (
                    f"Open Document Review tab to view selected evidence: Page {citation.page or 1}."
                )
                st.rerun()

    if view_model.counterparty_arguments:
        st.subheader("Possible Counterparty Arguments")
        st.dataframe(
            [
                {
                    "Possible argument": argument.argument,
                    "Evidence to collect": argument.evidence_needed,
                    "Safe response strategy": argument.safe_response,
                }
                for argument in view_model.counterparty_arguments
            ],
            hide_index=True,
            use_container_width=True,
        )


def _render_sources(view_model: ReportViewModel) -> None:
    st.subheader("Uploaded Document Citations")
    if view_model.uploaded_document_citations:
        st.dataframe(
            [
                {
                    "Citation": citation.citation_id,
                    "Page": citation.page,
                    "Quote preview": citation.quote,
                    "Used for": citation.section_label or "Document evidence",
                }
                for citation in view_model.uploaded_document_citations
            ],
            hide_index=True,
            use_container_width=True,
        )
        for citation in view_model.uploaded_document_citations:
            if st.button(
                f"View {citation.section_label or citation.citation_id}",
                key=f"citation-view-{citation.citation_id}",
            ):
                _select_document_citation(citation.citation_id, citation.page)
                st.session_state["nl_document_view_message"] = (
                    f"Open Document Review tab to view selected evidence: Page {citation.page or 1}."
                )
                st.rerun()
    else:
        st.info("No uploaded-document citations were produced.")

    st.subheader("Legal / Demo Corpus Citations")
    if get_settings().embedding_backend.lower() == "hash":
        st.info(
            "Offline demo retrieval mode is active. Results use lightweight hashing retrieval for reproducibility."
        )
    if view_model.legal_corpus_citations:
        st.dataframe(
            [
                {
                    "Title": citation.title,
                    "Domain": citation.domain,
                    "Jurisdiction": citation.jurisdiction,
                    "Source file": citation.source_file,
                    "Quote preview": citation.quote_preview,
                    "Corpus mode": display_label(citation.corpus_mode),
                }
                for citation in view_model.legal_corpus_citations
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.warning("No local corpus source was retrieved.")


def _render_law_cross_reference(view_model: ReportViewModel) -> None:
    st.warning(
        "NyayaLens identifies potentially relevant provisions and missing facts. "
        "It does not determine that a law has been broken."
    )
    if not view_model.law_cross_references:
        st.info("No law-pack cross-reference matched the current facts.")
        return
    st.dataframe(
        [
            {
                "Legal area": row.legal_area,
                "Potential source/provision": row.potential_source,
                "Why relevant": row.why_relevant,
                "Matched facts": row.matched_facts,
                "Missing facts": row.missing_facts,
                "Implication level": row.implication_level,
                "Confidence": row.confidence,
                "Citations": row.citations,
                "Human review": row.human_review,
            }
            for row in view_model.law_cross_references
        ],
        hide_index=True,
        use_container_width=True,
    )


def _render_drafts(report: FinalReport, view_model: ReportViewModel) -> None:
    st.subheader("Safe Next Steps")
    for index, step in enumerate(view_model.action_plan, start=1):
        st.checkbox(step, value=False, key=f"next-step-{index}")

    st.subheader("Evidence Checklist")
    for index, item in enumerate(view_model.evidence_checklist, start=1):
        st.checkbox(item, value=False, key=f"evidence-{index}")

    if view_model.draft_message:
        st.subheader("Safe Draft Message")
        st.text_area("Draft", view_model.draft_message, height=220)

    col_md, col_json = st.columns(2)
    col_md.download_button(
        "Download markdown report",
        data=markdown_report(report, view_model),
        file_name="nyayalens_report.md",
        mime="text/markdown",
    )
    col_json.download_button(
        "Download JSON report",
        data=json_report(view_model),
        file_name="nyayalens_report.json",
        mime="application/json",
    )


def _render_trust(report: FinalReport, view_model: ReportViewModel) -> None:
    panel = view_model.trust_panel
    st.subheader("Evaluation / Trust")
    columns = st.columns(4)
    columns[0].metric("Confidence", panel.confidence)
    columns[1].metric("Corpus mode", panel.corpus_mode)
    columns[2].metric("Retrieval mode", panel.retrieval_mode)
    columns[3].metric("Human review", "Yes" if panel.human_review_needed else "No")

    st.markdown("**Why confidence is limited**")
    if panel.uncertainty_reasons:
        for reason in panel.uncertainty_reasons:
            st.write(f"- {reason}")
    else:
        st.write("No major uncertainty reasons were produced.")

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**Confidence signals**")
        for reason in panel.confidence_reasons:
            st.write(f"- {reason}")
        st.write(f"- Citation coverage: {panel.citation_coverage}")
        st.write(f"- Safety status: {panel.safety_status}")
        st.write(f"- Hallucination guard: {panel.hallucination_guard_status}")
        st.write(f"- Official corpus coverage: {panel.official_corpus_coverage}")
        st.write(f"- Criminal-law screening basis: {panel.criminal_law_screening_basis}")
    with col_right:
        st.markdown("**Human review**")
        st.write(f"Suggested reviewer: {panel.suggested_reviewer}")
        if panel.human_review_reasons:
            for reason in panel.human_review_reasons:
                st.write(f"- {reason}")
        else:
            st.write("No mandatory human review signal was triggered for this demo report.")
        if panel.law_packs_loaded:
            st.markdown("**Law packs loaded**")
            for pack in panel.law_packs_loaded:
                st.write(f"- {pack}")
        if panel.law_pack_version_dates:
            st.caption("Law pack version dates: " + ", ".join(panel.law_pack_version_dates))

    st.markdown("**Official Law Pack Coverage**")
    st.caption(
        "NyayaLens uses official law packs where available. Missing or demo-only packs lower "
        "confidence and are shown here."
    )
    if panel.law_pack_coverage:
        st.dataframe(
            [
                {
                    "Law pack": row.expected_title,
                    "Status": display_label(row.status),
                    "Chunks": row.chunks_count,
                    "Mode": display_label(row.corpus_mode),
                    "Notes": "; ".join(row.warnings[:2]) or "Loaded.",
                }
                for row in panel.law_pack_coverage
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No law-pack manifest coverage rows were produced.")

    with st.expander("Missing facts", expanded=False):
        if report.missing_facts:
            for fact in report.missing_facts:
                st.write(f"- {fact}")
        else:
            st.write("No missing facts listed.")


def _render_debug(report: FinalReport, view_model: ReportViewModel) -> None:
    st.subheader("Raw Enums")
    st.json(
        {
            "issue_type": report.issue_detected.issue_type,
            "domain": report.issue_detected.domain,
            "document_type": report.extracted_facts.document_type,
            "expert_route": model_to_dict(report.expert_route),
        }
    )

    st.subheader("All Extracted Clauses")
    st.dataframe(view_model.debug_payload["raw_extracted_clauses"], hide_index=True, use_container_width=True)

    with st.expander("Rule Checks", expanded=False):
        st.json(view_model.debug_payload["rule_checks"])
    with st.expander("Potential Provision Matches", expanded=False):
        st.json(view_model.debug_payload["potential_provision_matches"])
    with st.expander("Retrieved Source Metadata", expanded=False):
        st.json(view_model.debug_payload["retrieved_source_metadata"])
    with st.expander("Audit Trace", expanded=False):
        st.json(view_model.debug_payload["audit_trace"])
    with st.expander("Verifier Result", expanded=False):
        st.json(view_model.debug_payload["verifier"])
    with st.expander("Raw JSON Output", expanded=False):
        st.json(json.loads(raw_json_report(report)))


def render_report(
    report: FinalReport,
    *,
    document_bytes: bytes | None = None,
    content_type: str | None = None,
    page_texts: list[tuple[int, str]] | None = None,
) -> None:
    view_model = to_report_view_model(report)
    st.info(report.disclaimer)
    st.caption(report.demo_corpus_notice)

    overview, risks, document, sources, law_cross_reference, drafts, trust, debug = st.tabs(
        [
            "Overview",
            "Risks & Remedies",
            "Document Review",
            "Sources & Citations",
            "Law Cross-Reference",
            "Drafts & Checklist",
            "Evaluation / Trust",
            "Audit / Debug",
        ]
    )
    with overview:
        _render_overview(report, view_model)
    with risks:
        _render_risks(view_model)
    with document:
        render_document_viewer(
            view_model,
            document_bytes=document_bytes,
            content_type=content_type,
            page_texts=page_texts or [(1, "")],
        )
    with sources:
        _render_sources(view_model)
    with law_cross_reference:
        _render_law_cross_reference(view_model)
    with drafts:
        _render_drafts(report, view_model)
    with trust:
        _render_trust(report, view_model)
    with debug:
        _render_debug(report, view_model)
