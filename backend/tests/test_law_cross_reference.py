from __future__ import annotations

from backend.app.agents.graph import run_analysis
from backend.app.core.schemas import (
    DocumentAnalysis,
    IssueAnalysis,
    JurisdictionResult,
    UserContext,
)
from backend.app.documents.clause_extractor import extract_document_analysis
from backend.app.explainability.report_view_model import to_report_view_model
from backend.app.law_packs.law_pack_loader import law_pack_status, load_law_sections
from backend.app.legal_matcher.matcher import match_potential_provisions
from backend.tests.test_freelance_service_agreement import FREELANCE_AGREEMENT


def _freelance_document() -> DocumentAnalysis:
    return extract_document_analysis(FREELANCE_AGREEMENT)


def _matches(query: str, dispute_date: str | None = None):
    context = UserContext(
        state="Maharashtra",
        city="Mumbai",
        user_role="freelancer",
        selected_dispute_type="auto-detect",
        query=query,
        dispute_date=dispute_date,
    )
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="demo_freelance_agreement.txt",
        context=context,
        persist=False,
    )
    return report.potential_provision_matches


def test_bns_preferred_after_2024_07_01() -> None:
    matches = _matches("The client used a forged invoice and fake signature.", "2024-07-02")
    criminal = [match for match in matches if match.legal_area == "criminal_screening"]
    assert criminal
    assert any(match.act_name == "Bharatiya Nyaya Sanhita, 2023" for match in criminal)
    assert all("Indian Penal Code" not in match.act_name for match in criminal[:1])


def test_ipc_only_historical_before_2024_07_01() -> None:
    matches = _matches("The client used a forged invoice and fake signature.", "2024-06-30")
    criminal = [match for match in matches if match.legal_area == "criminal_screening"]
    assert criminal
    assert criminal[0].act_name == "Indian Penal Code, 1860"


def test_unpaid_payment_does_not_trigger_criminal_without_fraud_or_threat() -> None:
    matches = _matches("I have not been paid for the last invoice.", "2026-01-01")
    assert all(match.legal_area != "criminal_screening" for match in matches)


def test_freelance_payment_matches_contract_area() -> None:
    matches = _matches("I have not been paid for the last invoice.")
    assert any(match.legal_area == "contract_payment" for match in matches)
    assert any(match.implication_level == "possible_civil_breach" for match in matches)


def test_freelance_independent_contractor_triggers_classification_review() -> None:
    matches = _matches("payment pending")
    assert any(match.legal_area == "labour_classification" for match in matches)
    classification = next(match for match in matches if match.legal_area == "labour_classification")
    assert "working hours" in classification.missing_facts
    assert "does not assume" in classification.why_relevant.lower()


def test_tds_deduction_not_deposit_deduction() -> None:
    matches = _matches("Please review the TDS deducted from payment.")
    assert any(match.legal_area == "contract_payment" for match in matches)
    assert all(match.legal_area != "tenancy_deposit" for match in matches)


def test_constitution_not_primary_for_private_contract() -> None:
    matches = _matches("Private company has not paid my invoice.")
    assert all(match.legal_area != "constitution_public_law" for match in matches)


def test_public_authority_issue_triggers_constitution_pack() -> None:
    document = DocumentAnalysis(document_type="plain_text_description", detected_domain="unknown")
    matches = match_potential_provisions(
        issue=IssueAnalysis(domain="unknown", issue_type="public_authority_abuse", confidence="medium"),
        document=document,
        context=UserContext(counterparty="government public authority", query="public official denied a scheme benefit"),
        jurisdiction=JurisdictionResult(),
        user_text="public official denied a scheme benefit",
    )
    assert any(match.legal_area == "constitution_public_law" for match in matches)


def test_potential_provision_match_has_missing_facts() -> None:
    matches = _matches("I have not been paid for the last invoice.")
    assert matches
    assert all(match.missing_facts for match in matches)


def test_law_cross_reference_never_says_law_broken() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="demo_freelance_agreement.txt",
        context=UserContext(user_role="freelancer", query="I have not been paid."),
        persist=False,
    )
    payload = " ".join(
        [match.why_relevant + " " + match.source_quote for match in report.potential_provision_matches]
    ).lower()
    assert "law is broken" not in payload
    assert "violation proven" not in payload
    assert "potentially relevant" in payload


def test_loaded_law_pack_metadata_contains_effective_date_and_source() -> None:
    sections = load_law_sections()
    assert sections
    assert all(section.effective_from for section in sections)
    assert all(section.version_date for section in sections)
    assert all(section.source_authority for section in sections)


def test_official_corpus_mode_displayed_in_trust_panel() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="demo_freelance_agreement.txt",
        context=UserContext(user_role="freelancer", query="I have not been paid."),
        persist=False,
    )
    vm = to_report_view_model(report)
    status = law_pack_status()
    assert vm.trust_panel.official_corpus_coverage in {
        "Demo law-pack matches only",
        "Official law-pack matches only",
        "Mixed demo/official law-pack matches",
    }
    assert status.law_packs_loaded
    assert vm.trust_panel.law_packs_loaded
