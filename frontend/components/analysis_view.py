from __future__ import annotations

import streamlit as st
from backend.app.core.schemas import FinalReport

from frontend.components.citation_view import render_sources
from frontend.components.risk_view import render_risks


def render_report(report: FinalReport) -> None:
    st.success(report.disclaimer)
    st.caption(report.demo_corpus_notice)

    col1, col2, col3 = st.columns(3)
    col1.metric("Issue", report.issue_detected.issue_type)
    col2.metric("Domain", report.issue_detected.domain)
    col3.metric("Confidence", report.confidence)

    st.subheader("Extracted Facts")
    st.write(f"Document type: `{report.extracted_facts.document_type}`")
    if report.extracted_facts.parties:
        st.write("Parties: " + ", ".join(report.extracted_facts.parties))
    if report.extracted_facts.dates:
        st.write("Dates: " + ", ".join(report.extracted_facts.dates))
    if report.extracted_facts.amounts:
        st.write("Amounts: " + ", ".join(report.extracted_facts.amounts))

    st.markdown("**Clauses**")
    for clause in report.extracted_facts.extracted_clauses:
        with st.container(border=True):
            st.write(f"`{clause.name}`: {clause.value}")
            st.caption(f"confidence={clause.confidence} | page={clause.page or 'n/a'}")
            st.write(clause.raw_text)
            if clause.risk_hint:
                st.caption(clause.risk_hint)

    st.subheader("Missing Facts")
    if report.missing_facts:
        for fact in report.missing_facts:
            st.write(f"- {fact}")
    else:
        st.write("No missing facts listed.")

    st.subheader("Expert Route")
    st.write(f"Primary: `{report.expert_route.primary_expert}`")
    st.write("Secondary: " + ", ".join(report.expert_route.secondary_experts))
    st.caption(report.expert_route.route_reason)

    st.subheader("Jurisdiction")
    st.write(f"State: `{report.jurisdiction.state or 'missing'}` | City: `{report.jurisdiction.city or 'missing'}`")
    if report.jurisdiction.jurisdiction_clause:
        st.code(report.jurisdiction.jurisdiction_clause)
    for warning in report.jurisdiction.warnings:
        st.warning(warning)

    render_sources(report.retrieved_sources, report.citations)
    render_risks(report.risk_flags, report.rule_checks)

    st.subheader("Safe Next Steps")
    for step in report.remedy_plan.steps:
        st.write(f"- {step}")
    st.markdown("**Evidence Checklist**")
    for item in report.remedy_plan.evidence_checklist:
        st.write(f"- {item}")
    if report.remedy_plan.draft_message:
        st.markdown("**Safe Draft Message**")
        st.text_area("Draft", report.remedy_plan.draft_message, height=220)

    st.subheader("Uncertainties")
    for item in report.uncertainties:
        st.write(f"- {item}")
    if report.verifier.warnings:
        st.warning(report.verifier.conservative_message or "Verifier warnings found.")
        for warning in report.verifier.warnings:
            st.write(f"- {warning}")

    with st.expander("Audit Trace", expanded=False):
        for entry in report.audit_trace:
            st.write(f"**{entry.node_name}** - {entry.timestamp}")
            st.caption(f"Input: {entry.input_summary}")
            st.caption(f"Output: {entry.output_summary}")
            for warning in entry.warnings:
                st.warning(warning)
