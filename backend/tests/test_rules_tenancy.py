from __future__ import annotations

from pathlib import Path

from backend.app.agents.jurisdiction_router import route_jurisdiction
from backend.app.core.schemas import DocumentAnalysis, UserContext
from backend.app.documents.clause_extractor import extract_document_analysis
from backend.app.rules.tenancy_rules import evaluate_tenancy_rules

ROOT = Path(__file__).resolve().parents[2]


def test_deposit_deduction_rule() -> None:
    text = (ROOT / "data/raw/sample_uploads/sample_rent_agreement.txt").read_text()
    doc = extract_document_analysis(text, page_texts=[(1, text)])
    context = UserContext(query="Landlord deducted deposit without itemized bill.")
    jurisdiction = route_jurisdiction(text, doc, context)
    rules = evaluate_tenancy_rules(doc, context, jurisdiction, "deposit_deduction")
    assert any(rule.id == "tenancy_deposit_itemization" and rule.severity == "high" for rule in rules)


def test_jurisdiction_missing_confidence_reduction() -> None:
    doc = DocumentAnalysis(document_type="tenancy_document", detected_domain="tenancy")
    jurisdiction = route_jurisdiction("Tenant paid deposit. No city stated.", doc, UserContext())
    rules = evaluate_tenancy_rules(doc, UserContext(query="deposit issue"), jurisdiction, "deposit_deduction")
    assert jurisdiction.confidence == "low"
    assert any(rule.id == "tenancy_jurisdiction_missing" for rule in rules)
