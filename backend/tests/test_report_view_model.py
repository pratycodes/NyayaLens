from __future__ import annotations

from backend.app.agents.graph import run_analysis
from backend.app.core.schemas import UserContext
from backend.app.explainability.report_view_model import GENERAL_INFO_LABEL, to_report_view_model
from backend.tests.test_freelance_service_agreement import FREELANCE_AGREEMENT


def _freelance_report():
    return run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            selected_dispute_type="auto-detect",
        ),
        persist=False,
    )


def test_report_view_model_has_summary_cards() -> None:
    vm = to_report_view_model(_freelance_report())
    cards = {card.label: card.value for card in vm.summary_cards}
    assert cards["Issue"] == "Contract payment review"
    assert cards["Domain"] == "Contract payment"
    assert cards["Document type"] == "Freelance/service agreement"


def test_key_facts_table_limited_and_relevant() -> None:
    vm = to_report_view_model(_freelance_report())
    facts = {row.fact for row in vm.key_facts_table}
    assert len(vm.key_facts_table) <= 10
    assert "Payment/consideration clause" in facts
    assert "Invoice timing" in facts
    assert "Compensation details" in facts
    assert "Jurisdiction clause" in facts
    assert "Freelancer role" not in facts
    assert all("freelancer_role" not in row.fact for row in vm.key_facts_table)


def test_risk_table_rows_have_citations_or_general_info() -> None:
    vm = to_report_view_model(_freelance_report())
    assert vm.risks_table
    for row in vm.risks_table:
        assert row.evidence
        assert row.next_step
        assert row.citation_labels
        assert (
            row.document_citation_ids
            or row.legal_citation_ids
            or GENERAL_INFO_LABEL in row.citation_labels
        )


def test_important_sections_for_freelance_agreement() -> None:
    vm = to_report_view_model(_freelance_report())
    categories = {section.category for section in vm.important_sections}
    titles = {section.title for section in vm.important_sections}
    assert "Payment" in categories
    assert "Invoice timing" in titles
    assert "Compensation details" in titles
    assert "TDS/deduction clause" in titles
    assert "Independent contractor relationship" in titles
    assert "Arbitration clause" in titles
    assert "Jurisdiction clause" in titles


def test_uploaded_document_citations_have_page_and_quote() -> None:
    vm = to_report_view_model(_freelance_report())
    assert vm.uploaded_document_citations
    for citation in vm.uploaded_document_citations:
        assert citation.page is not None
        assert citation.quote


def test_debug_payload_contains_raw_clauses() -> None:
    vm = to_report_view_model(_freelance_report())
    assert vm.debug_payload["raw_extracted_clauses"]
    key_fact_names = {row.fact for row in vm.key_facts_table}
    assert "freelancer_role" not in key_fact_names


def test_missing_clause_page_is_not_faked_as_page_one() -> None:
    report = _freelance_report()
    target = next(clause for clause in report.extracted_facts.extracted_clauses if clause.name == "tds_clause")
    target.page = None
    vm = to_report_view_model(report)
    citation = next(
        item for item in vm.uploaded_document_citations if item.clause_id == "tds_clause"
    )
    assert citation.page is None
    fact = next(row for row in vm.key_facts_table if row.fact == "TDS/deduction clause")
    assert fact.source == "Document page unavailable"
