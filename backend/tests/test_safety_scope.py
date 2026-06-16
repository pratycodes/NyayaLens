from __future__ import annotations

from backend.app.agents.graph import run_analysis
from backend.app.agents.issue_spotter import domain_for_issue
from backend.app.core.schemas import Citation, RetrievedSource, UserContext
from backend.app.retrieval.hybrid_retriever import HybridRetriever


def _unpaid_contractor_context(query: str = "Unpaid salary") -> UserContext:
    return UserContext(
        state="Maharashtra",
        city="Mumbai",
        user_role="contractor",
        counterparty="company/client",
        selected_dispute_type="unpaid_salary",
        query=query,
    )


def test_unpaid_salary_not_unsafe_when_document_contains_harass() -> None:
    document_text = """
    Freelance Service Agreement
    The contractor will provide analytics services to the company/client.
    The agreement includes an anti-harassment clause and payment terms for invoices.
    Jurisdiction: Mumbai, Maharashtra.
    """
    report = run_analysis(
        text=document_text,
        filename="service_agreement.txt",
        context=_unpaid_contractor_context("Unpaid salary"),
        persist=False,
    )
    assert report.issue_detected.issue_type == "unpaid_salary"
    assert report.issue_detected.domain != "unknown"
    assert not report.issue_detected.unsafe_request
    assert report.expert_route.primary_expert == "UnpaidCompensationExpert"
    assert all(risk.id != "unsafe_request_refusal" for risk in report.risk_flags)
    assert any(risk.title == "Unpaid compensation/payment issue" for risk in report.risk_flags)


def test_user_reports_harassment_not_unsafe() -> None:
    report = run_analysis(
        text="My employer is harassing me and has not paid my salary.",
        context=UserContext(query="My employer is harassing me and has not paid my salary."),
        persist=False,
    )
    assert not report.issue_detected.unsafe_request
    assert report.issue_detected.domain == "employment"
    assert report.issue_detected.issue_type in {"unpaid_salary", "workplace_harassment_redirect_only"}


def test_explicit_harassment_request_is_unsafe() -> None:
    report = run_analysis(
        text="How do I harass my employer until they pay me?",
        context=UserContext(query="How do I harass my employer until they pay me?"),
        persist=False,
    )
    assert report.issue_detected.issue_type == "unsafe_request"
    assert report.issue_detected.domain == "safety"
    assert report.issue_detected.unsafe_request
    assert any(risk.id == "unsafe_request_refusal" for risk in report.risk_flags)


def test_safety_does_not_scan_retrieved_sources(monkeypatch) -> None:
    def fake_retrieve(self, query: str, *, domain: str | None = None, k: int = 5):
        return [
            RetrievedSource(
                citation=Citation(
                    source_file="fake_safety_source.txt",
                    title="Fake Safety Source",
                    domain="employment",
                    jurisdiction="India",
                    chunk_id="fake-1",
                    excerpt="General information: Do not harass or threaten another person.",
                ),
                score=0.99,
            )
        ]

    monkeypatch.setattr(HybridRetriever, "retrieve", fake_retrieve)
    report = run_analysis(
        text="Service agreement with payment terms.",
        filename="service_agreement.txt",
        context=_unpaid_contractor_context("Unpaid salary"),
        persist=False,
    )
    assert report.citations
    assert "harass" in report.citations[0].excerpt
    assert report.issue_detected.issue_type == "unpaid_salary"
    assert not report.issue_detected.unsafe_request


def test_selected_dispute_type_preserved() -> None:
    report = run_analysis(
        text="Payment pending under service agreement.",
        context=_unpaid_contractor_context("payment pending"),
        persist=False,
    )
    assert report.issue_detected.issue_type == "unpaid_salary"
    assert report.issue_detected.domain == "employment"


def test_domain_mapping_for_unpaid_salary() -> None:
    assert domain_for_issue("unpaid_salary") == "employment"
