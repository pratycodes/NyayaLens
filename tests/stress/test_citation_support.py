from __future__ import annotations

import re
from pathlib import Path

import pytest
from backend.app.agents.graph import run_analysis
from backend.app.core.schemas import UserContext
from backend.app.documents.parsers import parse_document
from backend.app.explainability.report_view_model import GENERAL_INFO_LABEL, to_report_view_model
from frontend.components.pdf_viewer import render_pdf_page_to_png
from scripts.generate_stress_docs import generate_stress_docs

FIXTURE_DIR = Path("tests/fixtures/stress_docs")


@pytest.fixture(scope="module", autouse=True)
def _ensure_stress_docs() -> None:
    generate_stress_docs(FIXTURE_DIR)


def _freelance_pdf_report():
    parsed = parse_document(FIXTURE_DIR / "freelance_agreement.pdf")
    return run_analysis(
        text=parsed.text,
        filename="freelance_agreement.pdf",
        page_texts=parsed.page_texts,
        parser_warnings=parsed.warnings,
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="freelancer",
            query="I have not been paid.",
        ),
        persist=False,
    )


def test_every_risk_has_citation_or_general_info_label() -> None:
    vm = to_report_view_model(_freelance_pdf_report())

    assert vm.risks_table
    for risk in vm.risks_table:
        assert risk.evidence
        assert risk.next_step
        assert risk.document_citation_ids or risk.legal_citation_ids or risk.general_info_label == GENERAL_INFO_LABEL


def test_uploaded_document_citations_have_page_or_no_page_reason() -> None:
    vm = to_report_view_model(_freelance_pdf_report())

    assert vm.uploaded_document_citations
    for citation in vm.uploaded_document_citations:
        assert citation.quote
        assert citation.page is not None or "page unavailable" in citation.section_label.lower()


def test_quote_search_succeeds_for_text_pdf() -> None:
    document_bytes = (FIXTURE_DIR / "freelance_agreement.pdf").read_bytes()
    png, highlighted = render_pdf_page_to_png(document_bytes, 1, "Invoice shall be generated")

    assert png.startswith(b"\x89PNG")
    assert highlighted


def test_failed_quote_search_gives_page_level_fallback() -> None:
    document_bytes = (FIXTURE_DIR / "freelance_agreement.pdf").read_bytes()
    png, highlighted = render_pdf_page_to_png(document_bytes, 1, "quote not present in document")

    assert png.startswith(b"\x89PNG")
    assert not highlighted


def test_no_risk_contains_unsupported_exact_law_section() -> None:
    report = _freelance_pdf_report()
    vm = to_report_view_model(report)
    text = " ".join(
        [
            " ".join(risk.why_it_matters for risk in vm.risks_table),
            " ".join(risk.evidence for risk in vm.risks_table),
            report.remedy_plan.draft_message or "",
        ]
    )

    assert not re.search(r"\bSection\s+999\b", text, flags=re.IGNORECASE)
    assert "NyayaLens Act" not in text
