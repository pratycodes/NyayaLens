from __future__ import annotations

from pathlib import Path

from backend.app.documents.clause_extractor import extract_document_analysis

ROOT = Path(__file__).resolve().parents[2]


def test_clause_extraction_employment_sample() -> None:
    text = (ROOT / "data/raw/sample_uploads/sample_employment_contract.txt").read_text()
    analysis = extract_document_analysis(text, page_texts=[(1, text)])
    names = {clause.name for clause in analysis.extracted_clauses}
    assert analysis.detected_domain == "employment"
    assert "notice_period" in names
    assert "bond_amount" in names
    assert "non_compete_duration" in names
    assert "full_and_final_settlement" in names
    assert "jurisdiction_clause" in names


def test_clause_extraction_tenancy_sample() -> None:
    text = (ROOT / "data/raw/sample_uploads/sample_rent_agreement.txt").read_text()
    analysis = extract_document_analysis(text, page_texts=[(1, text)])
    names = {clause.name for clause in analysis.extracted_clauses}
    assert analysis.detected_domain == "tenancy"
    assert "rent_amount" in names
    assert "security_deposit" in names
    assert "lock_in_period" in names
    assert "notice_period" in names
    assert "jurisdiction_clause" in names
