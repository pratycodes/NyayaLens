from __future__ import annotations

import pytest
from backend.app.agents.graph import run_analysis
from backend.app.agents.human_review import evaluate_human_review
from backend.app.agents.issue_domain_consistency import validate_issue_domain
from backend.app.agents.remedy_router import route_remedy
from backend.app.core.schemas import DocumentAnalysis, IssueAnalysis, RiskFlag, UserContext
from backend.app.corpus.ingest import ingest_corpus
from backend.app.explainability.report_export import json_report, markdown_report
from backend.app.explainability.report_view_model import to_report_view_model
from backend.tests.test_freelance_service_agreement import FREELANCE_AGREEMENT


def _freelance_report(query: str = ""):
    return run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="demo_freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="freelancer",
            selected_dispute_type="auto-detect",
            query=query,
        ),
        persist=False,
    )


def test_report_view_model_includes_trust_and_modes() -> None:
    vm = to_report_view_model(_freelance_report())
    cards = {card.label: card.value for card in vm.summary_cards}
    assert cards["Corpus mode"] in {"Demo", "Mixed", "User-uploaded", "Official"}
    assert cards["Privacy mode"] == "Local/mock"
    assert vm.trust_panel.retrieval_mode
    assert vm.trust_panel.citation_coverage


def test_counterparty_arguments_for_freelance_payment_are_safe() -> None:
    vm = to_report_view_model(_freelance_report("I have not been paid."))
    assert vm.counterparty_arguments
    combined = " ".join(
        f"{row.argument} {row.safe_response}" for row in vm.counterparty_arguments
    ).lower()
    assert "threat" not in combined
    assert "blackmail" not in combined
    assert "deduction is tds" in combined


def test_markdown_and_json_exports_are_serializable_and_cited() -> None:
    report = _freelance_report()
    vm = to_report_view_model(report)
    markdown = markdown_report(report, vm)
    payload = json_report(vm)
    assert "not legal advice" in markdown.lower()
    assert "## Citations" in markdown
    assert "debug_payload" not in payload
    assert "Document p." in markdown or "Document page unavailable" in markdown


def test_issue_domain_consistency_blocks_freelance_tenancy_false_positive() -> None:
    issue = IssueAnalysis(domain="tenancy", issue_type="deposit_deduction", confidence="medium")
    document = DocumentAnalysis(
        document_type="freelance_service_agreement",
        detected_domain="contract_payment",
    )
    corrected = validate_issue_domain(
        issue,
        document=document,
        context=UserContext(user_role="contractor", query="TDS deducted"),
        user_text="TDS deducted",
        document_text="FREELANCE SERVICE AGREEMENT. TDS will be deducted as per applicable.",
    )
    assert corrected.domain == "contract_payment"
    assert corrected.issue_type == "contract_payment_review"


def test_employee_unpaid_salary_uses_hr_payroll() -> None:
    remedy = route_remedy(
        IssueAnalysis(domain="employment", issue_type="unpaid_salary", confidence="high"),
        [],
        UserContext(user_role="employee"),
    )
    assert "HR/Payroll Team" in (remedy.draft_message or "")
    assert "Company/Client/Accounts Team" not in (remedy.draft_message or "")


def test_tenancy_deposit_uses_landlord_deposit_language() -> None:
    remedy = route_remedy(
        IssueAnalysis(domain="tenancy", issue_type="deposit_deduction", confidence="high"),
        [],
        UserContext(user_role="tenant"),
    )
    text = " ".join(remedy.steps + remedy.evidence_checklist + [remedy.draft_message or ""]).lower()
    assert "landlord" in text
    assert "deposit" in text
    assert "invoice" not in text


def test_arbitration_clause_adds_human_review_and_route_step() -> None:
    report = _freelance_report()
    decision = evaluate_human_review(report)
    assert decision.needed
    assert any("arbitration" in reason.lower() for reason in decision.reasons)
    remedy = route_remedy(
        report.issue_detected,
        report.risk_flags,
        UserContext(user_role="freelancer"),
        document=report.extracted_facts,
        jurisdiction=report.jurisdiction,
    )
    assert any("arbitration" in step.lower() for step in remedy.steps)


def test_high_risk_triggers_human_review() -> None:
    report = _freelance_report("I have not been paid.")
    report.risk_flags.append(
        RiskFlag(
            id="test-high",
            title="Synthetic high risk",
            severity="high",
            confidence="high",
            explanation="General information from deterministic checks.",
            suggested_next_step="Seek human review.",
        )
    )
    assert evaluate_human_review(report).needed


def test_pdf_viewer_utility_renders_and_missing_quote_does_not_crash() -> None:
    fitz = pytest.importorskip("fitz")
    from frontend.components.pdf_viewer import render_pdf_page_to_png

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Payment shall be made in the last week.")
    document_bytes = pdf.tobytes()
    pdf.close()

    rendered, highlighted = render_pdf_page_to_png(document_bytes, 1, "Payment shall be made")
    assert rendered.startswith(b"\x89PNG")
    assert highlighted
    rendered, highlighted = render_pdf_page_to_png(document_bytes, 1, "missing quote")
    assert rendered.startswith(b"\x89PNG")
    assert not highlighted


def test_eval_script_runs_and_contains_metrics() -> None:
    from scripts.run_eval import run_eval

    summary = run_eval()
    assert summary["scenario_count"] >= 30
    assert "document_type_accuracy" in summary["metrics"]
    assert "false_unsafe_refusal_rate" in summary["metrics"]


def test_audit_trace_has_node_durations_and_analysis_id() -> None:
    report = _freelance_report()
    assert report.analysis_id
    assert report.audit_trace
    for entry in report.audit_trace:
        assert entry.analysis_id == report.analysis_id
        assert entry.duration_ms >= 0
        assert entry.started_at is not None


def test_demo_corpus_metadata_supported() -> None:
    chunks = ingest_corpus(include_demo=True, corpus_mode="demo")
    assert chunks
    assert {chunk.corpus_mode for chunk in chunks} == {"demo"}
    assert all(chunk.title for chunk in chunks)
