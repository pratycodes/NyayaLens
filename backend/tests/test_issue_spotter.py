from __future__ import annotations

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
