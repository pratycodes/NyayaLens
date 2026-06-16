from __future__ import annotations

from pathlib import Path

import pytest
from backend.app.agents.graph import run_analysis
from backend.app.core.errors import UnsupportedDocumentError
from backend.app.core.schemas import UserContext
from backend.app.documents.clause_extractor import extract_document_analysis
from backend.app.documents.parsers import parse_document
from scripts.generate_stress_docs import generate_stress_docs

FIXTURE_DIR = Path("tests/fixtures/stress_docs")


@pytest.fixture(scope="module", autouse=True)
def _ensure_stress_docs() -> None:
    generate_stress_docs(FIXTURE_DIR)


def test_empty_pdf_graceful_warning() -> None:
    parsed = parse_document(FIXTURE_DIR / "empty.pdf")

    assert parsed.page_texts
    assert not parsed.text.strip()
    assert any("No extractable PDF text" in warning for warning in parsed.warnings)


def test_corrupt_pdf_graceful_error() -> None:
    with pytest.raises(UnsupportedDocumentError) as exc:
        parse_document(FIXTURE_DIR / "corrupt.pdf")

    assert "PDF parsing failed" in str(exc.value)


def test_scanned_pdf_ocr_warning() -> None:
    parsed = parse_document(FIXTURE_DIR / "scanned_like.pdf")

    assert any("OCR may be required" in warning for warning in parsed.warnings)


def test_huge_pdf_page_warning() -> None:
    parsed = parse_document(FIXTURE_DIR / "large_multi_page.pdf")

    assert len(parsed.page_texts) > 20
    assert any("Large PDF warning" in warning for warning in parsed.warnings)


def test_mixed_domain_freelance_not_tenancy() -> None:
    parsed = parse_document(FIXTURE_DIR / "mixed_domain_freelance.pdf")
    report = run_analysis(
        text=parsed.text,
        filename="mixed_domain_freelance.pdf",
        page_texts=parsed.page_texts,
        parser_warnings=parsed.warnings,
        context=UserContext(user_role="freelancer", query="Payment pending."),
        persist=False,
    )

    assert report.extracted_facts.document_type == "freelance_service_agreement"
    assert report.issue_detected.domain == "contract_payment"
    assert report.issue_detected.issue_type != "deposit_deduction"


def test_tds_deduction_not_deposit_deduction() -> None:
    parsed = parse_document(FIXTURE_DIR / "mixed_domain_freelance.pdf")
    report = run_analysis(
        text=parsed.text,
        filename="mixed_domain_freelance.pdf",
        page_texts=parsed.page_texts,
        context=UserContext(user_role="freelancer", query="Review TDS deduction."),
        persist=False,
    )

    assert report.issue_detected.domain == "contract_payment"
    assert report.issue_detected.issue_type != "deposit_deduction"


def test_damages_not_repair_dispute() -> None:
    parsed = parse_document(FIXTURE_DIR / "mixed_domain_freelance.pdf")
    report = run_analysis(
        text=parsed.text,
        filename="mixed_domain_freelance.pdf",
        page_texts=parsed.page_texts,
        context=UserContext(user_role="freelancer", query="Review damages and invoice payment."),
        persist=False,
    )

    assert report.issue_detected.issue_type != "repair_dispute"
    assert report.issue_detected.domain != "tenancy"


def test_prompt_injection_inside_document_ignored() -> None:
    parsed = parse_document(FIXTURE_DIR / "prompt_injection_document.pdf")
    report = run_analysis(
        text=parsed.text,
        filename="prompt_injection_document.pdf",
        page_texts=parsed.page_texts,
        context=UserContext(user_role="freelancer", query="I have not been paid."),
        persist=False,
    )
    visible_text = " ".join(
        [
            report.issue_detected.issue_type,
            report.issue_detected.domain,
            " ".join(risk.explanation for risk in report.risk_flags),
            report.remedy_plan.draft_message or "",
        ]
    )

    assert report.issue_detected.issue_type == "unpaid_compensation"
    assert "Section 999" not in visible_text
    assert "NyayaLens Act" not in visible_text


def test_table_compensation_extracted() -> None:
    parsed = parse_document(FIXTURE_DIR / "table_compensation.pdf")
    analysis = extract_document_analysis(parsed.text, page_texts=parsed.page_texts)

    assert {"100000", "75000", "50000"}.issubset(set(analysis.amounts))
    assert any(clause.name == "compensation_clause" for clause in analysis.extracted_clauses)


def test_party_extraction_synthetic_freelance_agreement() -> None:
    parsed = parse_document(FIXTURE_DIR / "freelance_agreement.pdf")
    analysis = extract_document_analysis(parsed.text, page_texts=parsed.page_texts)

    assert analysis.structured_facts["company_or_client"] == "ACME DEMO SERVICES LLP"
    assert analysis.structured_facts["freelancer_name"] == "Demo Freelancer"
    assert analysis.structured_facts["role_or_designation"] == "Project Manager"
