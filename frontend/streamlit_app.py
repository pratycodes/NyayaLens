# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from backend.app.agents.graph import run_analysis
from backend.app.config import get_settings
from backend.app.core.schemas import UserContext
from backend.app.corpus.ingest import ingest_corpus
from backend.app.storage.sqlite import corpus_status, initialize_database

from frontend.components.analysis_view import render_report
from frontend.components.upload_panel import document_input

st.set_page_config(page_title="NyayaLens", page_icon="NL", layout="wide")

initialize_database()
settings = get_settings()

st.title("NyayaLens")
st.caption("Evidence-grounded legal issue triage for Indian employment, freelance-payment, and tenancy documents")

with st.sidebar:
    st.header("Context")
    selected = st.selectbox(
        "Dispute type",
        [
            "auto-detect",
            "employment_exit",
            "unpaid_salary",
            "bond_recovery",
            "notice_period",
            "non_compete",
            "full_and_final",
            "relieving_letter",
            "unpaid_compensation",
            "payment_withheld",
            "deposit_deduction",
            "eviction_notice",
            "rent_increase",
            "repair_dispute",
            "lock_in_dispute",
        ],
        format_func=lambda value: "Auto-detect" if value == "auto-detect" else value.replace("_", " ").title(),
    )
    state = st.text_input("State")
    city = st.text_input("City")
    user_role = st.selectbox(
        "User role",
        ["", "employee", "contractor", "freelancer", "consultant", "intern", "tenant", "landlord"],
    )
    query = st.text_area("Short dispute summary", height=100)
    with st.expander("Advanced context", expanded=False):
        counterparty = st.text_input("Counterparty")
        dispute_date = st.text_input("Dispute date")
        urgency = st.selectbox("Urgency", ["normal", "urgent", "critical"])
        remote_llm_enabled = settings.allow_remote_llm and settings.llm_provider.lower() != "mock"
        allow_remote_llm = st.checkbox(
            "Allow remote LLM for this analysis",
            value=False,
            disabled=not remote_llm_enabled,
            help=(
                "When enabled with remote LLM environment settings, document excerpts may be sent "
                "to the configured API provider. Leave off for local mock mode."
            ),
        )
        if st.button("Ingest demo corpus"):
            chunks = ingest_corpus(include_demo=True, corpus_mode="demo")
            st.success(f"Ingested {len(chunks)} chunks.")
        count, files = corpus_status()
        st.caption(f"Corpus chunks: {count} | Sources: {len(files)}")

document = document_input()

context = UserContext(
    state=state or None,
    city=city or None,
    user_role=user_role or None,
    counterparty=counterparty or None,
    dispute_date=dispute_date or None,
    urgency=urgency,
    selected_dispute_type=selected,
    query=query or None,
    allow_remote_llm=allow_remote_llm,
)

if st.button("Analyze", type="primary"):
    if not document.text.strip():
        st.error("Upload a document, load a sample, or enter a plain-text dispute description.")
    else:
        with st.spinner("Analyzing document locally..."):
            report = run_analysis(
                text=document.text,
                context=context,
                filename=document.filename,
                page_texts=document.page_texts,
                parser_warnings=document.warnings,
                persist=True,
            )
            st.session_state["report"] = report
            st.session_state["nl_document_bytes"] = document.document_bytes
            st.session_state["nl_document_content_type"] = document.content_type
            st.session_state["nl_document_page_texts"] = document.page_texts
            st.session_state["nl_document_filename"] = document.filename

if "report" in st.session_state:
    render_report(
        st.session_state["report"],
        document_bytes=st.session_state.get("nl_document_bytes"),
        content_type=st.session_state.get("nl_document_content_type"),
        page_texts=st.session_state.get("nl_document_page_texts"),
    )
    st.subheader("Ask Follow-Up")
    followup = st.text_input("Question about this report")
    if followup:
        st.info(
            "Use the report citations and missing-facts list as the basis for follow-up. "
            "NyayaLens does not provide legal advice or guaranteed outcomes."
        )
