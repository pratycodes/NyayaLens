from __future__ import annotations

from pathlib import Path

from backend.app.agents.graph import run_analysis
from backend.app.config import get_settings
from backend.app.core.schemas import UserContext
from backend.app.retrieval.embeddings import HashingEmbeddingModel, get_embedding_model

ROOT = Path(__file__).resolve().parents[2]


def _sample_report(sample_name: str, context: UserContext):
    text = (ROOT / "data/raw/sample_uploads" / sample_name).read_text()
    return run_analysis(text=text, filename=sample_name, context=context, persist=False)


def test_mock_mode_uses_lightweight_local_embeddings_by_default() -> None:
    get_settings.cache_clear()
    get_embedding_model.cache_clear()
    settings = get_settings()
    assert settings.llm_provider == "mock"
    assert not settings.allow_remote_llm
    assert isinstance(get_embedding_model(), HashingEmbeddingModel)


def test_sample_employment_report_is_showcase_ready() -> None:
    report = _sample_report(
        "sample_employment_contract.txt",
        UserContext(
            state="Karnataka",
            city="Bengaluru",
            user_role="employee",
            query="Company is withholding salary and asking for bond recovery.",
        ),
    )
    assert report.issue_detected.domain == "employment"
    assert report.issue_detected.issue_type == "bond_recovery"
    assert report.extracted_facts.extracted_clauses
    assert report.risk_flags
    assert report.citations
    assert report.missing_facts
    assert report.remedy_plan.steps
    assert "not legal advice" in report.disclaimer.lower()
    assert all("General information" in rule.explanation for rule in report.rule_checks)


def test_sample_tenancy_report_is_showcase_ready() -> None:
    report = _sample_report(
        "sample_rent_agreement.txt",
        UserContext(
            state="Karnataka",
            city="Bengaluru",
            user_role="tenant",
            query="Landlord deducted deposit without itemized bill.",
        ),
    )
    assert report.issue_detected.domain == "tenancy"
    assert report.issue_detected.issue_type == "deposit_deduction"
    assert report.extracted_facts.extracted_clauses
    assert report.risk_flags
    assert report.citations
    assert report.missing_facts
    assert report.remedy_plan.steps
    assert "not legal advice" in report.disclaimer.lower()
    assert all("General information" in rule.explanation for rule in report.rule_checks)
