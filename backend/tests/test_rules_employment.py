from __future__ import annotations

from pathlib import Path

from backend.app.agents.jurisdiction_router import route_jurisdiction
from backend.app.core.schemas import UserContext
from backend.app.documents.clause_extractor import extract_document_analysis
from backend.app.rules.employment_rules import evaluate_employment_rules

ROOT = Path(__file__).resolve().parents[2]


def test_employment_bond_and_non_compete_risk_rules() -> None:
    text = (ROOT / "data/raw/sample_uploads/sample_employment_contract.txt").read_text()
    doc = extract_document_analysis(text, page_texts=[(1, text)])
    context = UserContext(query="My salary is withheld and company wants bond recovery.")
    jurisdiction = route_jurisdiction(text, doc, context)
    rules = evaluate_employment_rules(doc, context, jurisdiction, "bond_recovery")
    ids = {rule.id for rule in rules if not rule.passed}
    assert "employment_bond_recovery" in ids
    assert "employment_non_compete_review" in ids
    assert "employment_long_notice_period" in ids
