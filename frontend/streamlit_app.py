# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from backend.app.agents.graph import run_analysis
from backend.app.core.schemas import UserContext
from backend.app.corpus.ingest import ingest_corpus
from backend.app.storage.sqlite import corpus_status, initialize_database

from frontend.components.analysis_view import render_report
from frontend.components.upload_panel import document_input

st.set_page_config(page_title="NyayaLens", page_icon="NL", layout="wide")

initialize_database()

st.title("NyayaLens")
st.caption("Explainable Legal-Rights Agent for Indian Employment Exit and Tenancy Disputes")

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
            "deposit_deduction",
            "eviction_notice",
            "rent_increase",
            "repair_dispute",
            "lock_in_dispute",
        ],
    )
    state = st.text_input("State")
    city = st.text_input("City")
    user_role = st.selectbox("User role", ["", "employee", "contractor", "intern", "tenant", "landlord"])
    counterparty = st.text_input("Counterparty")
    dispute_date = st.text_input("Dispute date")
    urgency = st.selectbox("Urgency", ["normal", "urgent", "critical"])
    query = st.text_area("Short dispute summary", height=100)
    if st.button("Ingest demo corpus"):
        chunks = ingest_corpus(include_demo=True)
        st.success(f"Ingested {len(chunks)} chunks.")
    count, files = corpus_status()
    st.caption(f"Corpus chunks: {count} | Sources: {len(files)}")

filename, text, page_texts, warnings = document_input()

context = UserContext(
    state=state or None,
    city=city or None,
    user_role=user_role or None,
    counterparty=counterparty or None,
    dispute_date=dispute_date or None,
    urgency=urgency,
    selected_dispute_type=selected,
    query=query or None,
)

if st.button("Analyze", type="primary"):
    if not text.strip():
        st.error("Upload a document, load a sample, or enter a plain-text dispute description.")
    else:
        with st.spinner("Analyzing document locally..."):
            report = run_analysis(
                text=text,
                context=context,
                filename=filename,
                page_texts=page_texts,
                parser_warnings=warnings,
                persist=True,
            )
            st.session_state["report"] = report

if "report" in st.session_state:
    render_report(st.session_state["report"])
    st.subheader("Ask Follow-Up")
    followup = st.text_input("Question about this report")
    if followup:
        st.info(
            "Use the report citations and missing-facts list as the basis for follow-up. "
            "NyayaLens does not provide legal advice or guaranteed outcomes."
        )
