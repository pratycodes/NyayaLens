from __future__ import annotations

from types import SimpleNamespace

import pytest
from backend.app.agents import issue_spotter
from backend.app.agents.issue_spotter import spot_issue
from backend.app.core.schemas import DocumentAnalysis, UserContext


def test_issue_spotter_employment_query() -> None:
    doc = DocumentAnalysis(document_type="employment_document", detected_domain="employment")
    issue = spot_issue("My employer is asking for bond recovery after resignation.", doc, UserContext())
    assert issue.domain == "employment"
    assert issue.issue_type == "bond_recovery"


def test_issue_spotter_tenancy_query() -> None:
    doc = DocumentAnalysis(document_type="tenancy_document", detected_domain="tenancy")
    issue = spot_issue("Landlord deducted my security deposit without itemized bill.", doc, UserContext())
    assert issue.domain == "tenancy"
    assert issue.issue_type == "deposit_deduction"


def test_notice_period_does_not_become_eviction_notice() -> None:
    doc = DocumentAnalysis(document_type="employment_document", detected_domain="employment")
    issue = spot_issue("I need help with my notice period.", doc, UserContext())
    assert issue.domain == "employment"
    assert issue.issue_type == "notice_period"


def test_remote_llm_requires_per_analysis_consent(monkeypatch: pytest.MonkeyPatch) -> None:
    doc = DocumentAnalysis(document_type="contract_document", detected_domain="unknown")
    monkeypatch.setattr(
        issue_spotter,
        "get_settings",
        lambda: SimpleNamespace(llm_provider="openai", allow_remote_llm=True),
    )
    monkeypatch.setattr(
        issue_spotter,
        "get_llm_provider",
        lambda: (_ for _ in ()).throw(AssertionError("remote provider should not be called")),
    )
    issue = spot_issue("Generic agreement review", doc, UserContext(allow_remote_llm=False))
    assert issue.issue_type in {"unknown", "employment_exit"}
