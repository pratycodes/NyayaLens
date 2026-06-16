from __future__ import annotations

from pathlib import Path

from backend.app.agents.graph import run_analysis
from backend.app.core.schemas import UserContext
from backend.app.documents.relevance import UNRELATED_PAYMENT_DOCUMENT_WARNING

ROOT = Path(__file__).resolve().parents[2]


def _contractor_unpaid_report(text: str = "I have not been paid yet"):
    return run_analysis(
        text=text,
        filename="plain_text.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="contractor",
            counterparty="company/client",
            selected_dispute_type="unpaid_salary",
            query="I have not been paid yet",
        ),
        persist=False,
    )


def test_unpaid_salary_plain_text_produces_risks() -> None:
    report = _contractor_unpaid_report()
    titles = {risk.title for risk in report.risk_flags}
    assert len(report.risk_flags) >= 3
    assert "Unpaid compensation/payment issue" in titles
    assert "Contractor/freelancer classification ambiguity" in titles
    assert "Missing payment evidence" in titles


def test_unpaid_salary_no_longer_says_no_risk_flags() -> None:
    report = _contractor_unpaid_report()
    serialized_report = report.model_dump_json()
    risk_view_source = (ROOT / "frontend/components/risk_view.py").read_text(encoding="utf-8")
    assert "No blocking risk flags" not in serialized_report
    assert "No blocking risk flags" not in risk_view_source


def test_contractor_unpaid_salary_route() -> None:
    report = _contractor_unpaid_report()
    assert report.expert_route.primary_expert == "UnpaidCompensationExpert"
    assert report.expert_route.secondary_experts == ["ContractClauseExpert", "VerifierExpert"]
    assert report.expert_route.route_reason == "Unpaid payment issue for a contractor/freelancer/service provider."


def test_resume_document_relevance_warning() -> None:
    resume_text = """
    Resume
    Curriculum Vitae
    Education: B.Tech Mathematics and Computing
    Skills: Python, Streamlit, FastAPI
    Projects: AI portfolio and legal assistant
    GitHub: example
    LinkedIn: example
    """
    report = _contractor_unpaid_report(text=resume_text)
    assert UNRELATED_PAYMENT_DOCUMENT_WARNING in report.extracted_facts.parser_warnings
    assert UNRELATED_PAYMENT_DOCUMENT_WARNING in report.uncertainties


def test_missing_facts_for_unpaid_salary_are_specific() -> None:
    report = _contractor_unpaid_report()
    missing = set(report.missing_facts)
    assert "amount unpaid" in missing
    assert "payment due date" in missing
    assert "whether the dispute is salary, stipend, invoice, consulting fee, freelance fee, or full-and-final settlement" in missing
    assert "proof of work delivered" in missing
    assert "written follow-up sent or not" in missing
    assert "dispute domain" not in missing


def test_contractor_draft_uses_payment_language_not_exit_settlement() -> None:
    report = _contractor_unpaid_report()
    draft = report.remedy_plan.draft_message or ""
    assert "pending payment" in draft.lower()
    assert "work/services" in draft
    assert "exit settlement" not in draft.lower()
