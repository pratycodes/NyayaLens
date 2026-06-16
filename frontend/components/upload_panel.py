from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
from backend.app.config import get_settings
from backend.app.documents.parsers import parse_document


@dataclass
class DocumentInputResult:
    filename: str
    text: str
    page_texts: list[tuple[int, str]]
    warnings: list[str]
    content_type: str | None = None
    document_bytes: bytes | None = None


def document_input() -> DocumentInputResult:
    uploaded = st.file_uploader("Upload document", type=["pdf", "docx", "txt"])
    sample = st.selectbox(
        "Or load sample",
        [
            "None",
            "Demo freelance agreement",
            "Demo employment exit agreement",
            "Demo rent agreement",
            "Sample employment contract",
            "Sample rent agreement",
        ],
    )
    typed_text = st.text_area("Plain-text dispute description", height=160)

    if uploaded is not None:
        settings = get_settings()
        suffix = Path(uploaded.name).suffix or ".txt"
        document_bytes = uploaded.getvalue()
        if len(document_bytes) > settings.max_upload_bytes:
            st.error(f"Upload exceeds {settings.max_upload_mb} MB local-demo limit.")
            return DocumentInputResult(
                filename=uploaded.name,
                text="",
                page_texts=[(1, "")],
                warnings=[f"Upload exceeds {settings.max_upload_mb} MB local-demo limit."],
                content_type=uploaded.type,
                document_bytes=None,
            )
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(document_bytes)
                tmp_path = Path(tmp.name)
            parsed = parse_document(tmp_path)
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)
        return DocumentInputResult(
            filename=uploaded.name,
            text=parsed.text,
            page_texts=parsed.page_texts,
            warnings=parsed.warnings,
            content_type=uploaded.type,
            document_bytes=document_bytes,
        )

    if sample != "None":
        root = Path(__file__).resolve().parents[2]
        sample_paths = {
            "Demo freelance agreement": "demo_freelance_agreement.txt",
            "Demo employment exit agreement": "demo_employment_exit_agreement.txt",
            "Demo rent agreement": "demo_rent_agreement.txt",
            "Sample employment contract": "sample_employment_contract.txt",
            "Sample rent agreement": "sample_rent_agreement.txt",
        }
        path = root / "data" / "raw" / "sample_uploads" / sample_paths[sample]
        parsed = parse_document(path)
        return DocumentInputResult(
            filename=path.name,
            text=parsed.text,
            page_texts=parsed.page_texts,
            warnings=parsed.warnings,
            content_type="text/plain",
            document_bytes=path.read_bytes(),
        )

    return DocumentInputResult(
        filename="plain_text.txt",
        text=typed_text,
        page_texts=[(1, typed_text)],
        warnings=[],
        content_type="text/plain",
        document_bytes=None,
    )
