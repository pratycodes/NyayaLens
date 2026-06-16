from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st
from backend.app.documents.parsers import parse_document


def document_input() -> tuple[str, str, list[tuple[int, str]], list[str]]:
    uploaded = st.file_uploader("Upload document", type=["pdf", "docx", "txt"])
    sample = st.selectbox(
        "Or load sample",
        ["None", "Sample employment contract", "Sample rent agreement"],
    )
    typed_text = st.text_area("Plain-text dispute description", height=160)

    if uploaded is not None:
        suffix = Path(uploaded.name).suffix or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = Path(tmp.name)
        parsed = parse_document(tmp_path)
        return uploaded.name, parsed.text, parsed.page_texts, parsed.warnings

    if sample != "None":
        root = Path(__file__).resolve().parents[2]
        path = (
            root / "data" / "raw" / "sample_uploads" / "sample_employment_contract.txt"
            if "employment" in sample.lower()
            else root / "data" / "raw" / "sample_uploads" / "sample_rent_agreement.txt"
        )
        parsed = parse_document(path)
        return path.name, parsed.text, parsed.page_texts, parsed.warnings

    return "plain_text.txt", typed_text, [(1, typed_text)], []
