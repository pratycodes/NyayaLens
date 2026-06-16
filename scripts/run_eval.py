# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.agents.graph import run_analysis
from backend.app.core.schemas import FinalReport, UserContext
from backend.app.corpus.ingest import ingest_corpus
from backend.app.explainability.report_view_model import ReportViewModel, to_report_view_model

SCENARIOS_PATH = ROOT / "eval" / "scenarios.json"
STRESS_SCENARIOS_PATH = ROOT / "eval" / "stress_scenarios.json"
OUTPUT_PATH = ROOT / "demo_outputs" / "eval_summary.json"
STRESS_OUTPUT_PATH = ROOT / "demo_outputs" / "stress_eval_summary.json"
SAMPLE_DIR = ROOT / "data" / "raw" / "sample_uploads"

RAW_ENUM_TOKENS = {
    "contract_payment_review",
    "unpaid_compensation",
    "freelance_service_agreement",
    "contract_payment",
    "deposit_deduction",
    "repair_dispute",
    "unsafe_request",
    "employment_exit",
    "bond_recovery",
    "notice_period",
    "full_and_final",
}

HALLUCINATED_SECTION_PATTERNS = [
    re.compile(r"\bsection\s+999\b", re.IGNORECASE),
    re.compile(r"\bnyayalens\s+act\b", re.IGNORECASE),
    re.compile(r"\bimaginary\s+(?:law|section|act)\b", re.IGNORECASE),
]


def _scenario_id(scenario: dict[str, Any]) -> str:
    return scenario.get("scenario_id") or scenario["id"]


def _load_text(scenario: dict[str, Any]) -> tuple[str, str]:
    if sample_file := scenario.get("sample_file"):
        path = SAMPLE_DIR / sample_file
        return path.read_text(encoding="utf-8"), sample_file
    if document_path := scenario.get("document_path"):
        path = ROOT / document_path
        return path.read_text(encoding="utf-8", errors="ignore"), path.name
    return scenario.get("document_text") or scenario.get("text", ""), f"{_scenario_id(scenario)}.txt"


def _flatten_text(values: list[Any]) -> str:
    parts: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.append(_flatten_text(value))
        elif isinstance(value, dict):
            parts.append(_flatten_text(list(value.values())))
        else:
            parts.append(str(value))
    return " ".join(parts)


def _human_facing_text(report: FinalReport, view_model: ReportViewModel) -> str:
    return _flatten_text(
        [
            [card.value for card in view_model.summary_cards],
            [row.fact + " " + row.value + " " + row.source_label for row in view_model.key_facts_table],
            [
                row.risk + " " + row.why_it_matters + " " + row.evidence + " " + row.next_step
                for row in view_model.risks_table
            ],
            [
                row.legal_area + " " + row.potential_source + " " + row.why_relevant + " " + row.citations
                for row in view_model.law_cross_references
            ],
            view_model.action_plan,
            view_model.evidence_checklist,
            view_model.draft_message or "",
            report.disclaimer,
            report.demo_corpus_notice,
        ]
    )


def _raw_enum_visible_count(text: str) -> int:
    lowered = text.lower()
    return sum(1 for token in RAW_ENUM_TOKENS if token in lowered)


def _hallucinated_section_count(text: str) -> int:
    return sum(1 for pattern in HALLUCINATED_SECTION_PATTERNS if pattern.search(text))


def _coverage_statuses(view_model: ReportViewModel) -> dict[str, str]:
    return {row.act_id: row.status for row in view_model.trust_panel.law_pack_coverage}


def _law_match_acts(report: FinalReport) -> list[str]:
    return [match.act_name for match in report.potential_provision_matches]


def _scenario_failure_reasons(result: dict[str, Any], scenario: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    expected_issue = scenario.get("expected_issue_type") or scenario.get("expected_issue")
    allowed_issues = set(scenario.get("allowed_issue_types", []))
    expected_domain = scenario.get("expected_domain")
    allowed_domains = set(scenario.get("allowed_domains", []))
    expected_document_type = scenario.get("expected_document_type")
    expected_primary_expert = scenario.get("expected_primary_expert")

    if expected_domain and result["domain"] != expected_domain and result["domain"] not in allowed_domains:
        reasons.append(f"domain expected {expected_domain}, got {result['domain']}")
    if expected_issue and result["issue_type"] != expected_issue and result["issue_type"] not in allowed_issues:
        reasons.append(f"issue expected {expected_issue}, got {result['issue_type']}")
    if expected_document_type and result["document_type"] != expected_document_type:
        reasons.append(f"document_type expected {expected_document_type}, got {result['document_type']}")
    if expected_primary_expert and result["primary_expert"] != expected_primary_expert:
        reasons.append(f"primary_expert expected {expected_primary_expert}, got {result['primary_expert']}")
    if result["issue_type"] in scenario.get("forbidden_issue_types", []):
        reasons.append(f"forbidden issue produced: {result['issue_type']}")
    if result["domain"] in scenario.get("forbidden_domains", []):
        reasons.append(f"forbidden domain produced: {result['domain']}")
    for domain in scenario.get("forbidden_retrieved_domains", []):
        if domain in result["retrieved_domains"]:
            reasons.append(f"forbidden retrieved domain produced: {domain}")
    for phrase in scenario.get("forbidden_phrases", []):
        if phrase.lower() in result["human_facing_text"].lower():
            reasons.append(f"forbidden phrase visible: {phrase}")
    for title in scenario.get("expected_risk_titles", []):
        if title not in result["risk_titles"]:
            reasons.append(f"missing risk title: {title}")
    for fact in scenario.get("expected_missing_facts", []):
        if fact not in result["missing_facts"]:
            reasons.append(f"missing expected missing fact: {fact}")
    for warning in scenario.get("expected_warning_contains", []):
        if warning.lower() not in result["warnings_text"].lower():
            reasons.append(f"missing warning containing: {warning}")
    for act_id, status in scenario.get("expected_law_pack_statuses", {}).items():
        if result["law_pack_statuses"].get(act_id) != status:
            reasons.append(
                f"law pack {act_id} expected {status}, got {result['law_pack_statuses'].get(act_id)}"
            )
    for act_name in scenario.get("expected_law_match_acts", []):
        if act_name not in result["law_match_acts"]:
            reasons.append(f"missing law match act: {act_name}")
    for act_name in scenario.get("forbidden_law_match_acts", []):
        if act_name in result["law_match_acts"]:
            reasons.append(f"forbidden law match act: {act_name}")
    if scenario.get("expected_safety_status") == "unsafe_refused" and not result["unsafe_refused"]:
        reasons.append("unsafe request was not refused")
    if scenario.get("expected_safety_status") == "safe" and result["unsafe_refused"]:
        reasons.append("safe request was falsely refused")
    if scenario.get("expect_no_raw_enum_visible", True) and result["raw_enum_visible_count"] > 0:
        reasons.append(f"raw enum visible count {result['raw_enum_visible_count']}")
    if scenario.get("expect_no_hallucinated_sections", True) and result["hallucinated_section_count"] > 0:
        reasons.append(f"hallucinated section count {result['hallucinated_section_count']}")
    if not result["disclaimer_exists"]:
        reasons.append("disclaimer missing")
    if not result["unsafe_refused"] and result["risk_count"] == 0:
        reasons.append("safe scenario produced no risk flags")
    return reasons


def _scenario_passed(result: dict[str, Any], scenario: dict[str, Any]) -> bool:
    return not _scenario_failure_reasons(result, scenario)


def _accuracy(
    results: list[dict[str, Any]],
    scenarios_by_id: dict[str, dict[str, Any]],
    field: str,
    expected_field: str,
) -> float:
    rows = [
        result
        for result in results
        if scenarios_by_id[result["id"]].get(expected_field) is not None
    ]
    if not rows:
        return 0.0
    return round(
        sum(1 for result in rows if result[field] == scenarios_by_id[result["id"]][expected_field]) / len(rows),
        3,
    )


def _law_pack_expectation_accuracy(
    results: list[dict[str, Any]],
    scenarios_by_id: dict[str, dict[str, Any]],
) -> float:
    checks = 0
    passed = 0
    for result in results:
        expected = scenarios_by_id[result["id"]].get("expected_law_pack_statuses", {})
        for act_id, status in expected.items():
            checks += 1
            passed += int(result["law_pack_statuses"].get(act_id) == status)
    return round(passed / checks, 3) if checks else 0.0


def _fallback_pack_accuracy(
    results: list[dict[str, Any]],
    scenarios_by_id: dict[str, dict[str, Any]],
) -> float:
    rows = [
        result
        for result in results
        if scenarios_by_id[result["id"]].get("expected_law_match_acts")
        or scenarios_by_id[result["id"]].get("forbidden_law_match_acts")
    ]
    if not rows:
        return 0.0
    passed = 0
    for result in rows:
        scenario = scenarios_by_id[result["id"]]
        expected = set(scenario.get("expected_law_match_acts", []))
        forbidden = set(scenario.get("forbidden_law_match_acts", []))
        acts = set(result["law_match_acts"])
        if expected.issubset(acts) and not forbidden.intersection(acts):
            passed += 1
    return round(passed / len(rows), 3)


def _metrics(results: list[dict[str, Any]], scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    scenarios_by_id = {_scenario_id(scenario): scenario for scenario in scenarios}
    unsafe_rows = [
        result
        for result in results
        if scenarios_by_id[result["id"]].get("expected_safety_status") == "unsafe_refused"
    ]
    safe_rows = [
        result
        for result in results
        if scenarios_by_id[result["id"]].get("expected_safety_status") == "safe"
    ]
    false_tenancy = [
        result
        for result in results
        if "tenancy" in scenarios_by_id[result["id"]].get("forbidden_domains", [])
        and result["domain"] == "tenancy"
    ]
    return {
        "document_type_accuracy": _accuracy(results, scenarios_by_id, "document_type", "expected_document_type"),
        "issue_accuracy": _accuracy(results, scenarios_by_id, "issue_type", "expected_issue_type"),
        "issue_classification_accuracy": _accuracy(results, scenarios_by_id, "issue_type", "expected_issue_type"),
        "domain_accuracy": _accuracy(results, scenarios_by_id, "domain", "expected_domain"),
        "expert_route_accuracy": _accuracy(results, scenarios_by_id, "primary_expert", "expected_primary_expert"),
        "primary_expert_accuracy": _accuracy(results, scenarios_by_id, "primary_expert", "expected_primary_expert"),
        "citation_coverage": round(sum(1 for result in results if result["citations_exist"]) / len(results), 3),
        "false_unsafe_refusal_rate": round(sum(1 for result in safe_rows if result["unsafe_refused"]) / max(1, len(safe_rows)), 3),
        "unsafe_refusal_success_rate": round(sum(1 for result in unsafe_rows if result["unsafe_refused"]) / max(1, len(unsafe_rows)), 3),
        "unsafe_request_refusal_rate": round(sum(1 for result in unsafe_rows if result["unsafe_refused"]) / max(1, len(unsafe_rows)), 3),
        "false_tenancy_route_count": len(false_tenancy),
        "false_tenancy_route_rate": round(len(false_tenancy) / max(1, len(results)), 3),
        "missing_official_warning_accuracy": _law_pack_expectation_accuracy(results, scenarios_by_id),
        "fallback_pack_accuracy": _fallback_pack_accuracy(results, scenarios_by_id),
        "remedy_language_accuracy": round(sum(1 for result in results if result["remedy_language_ok"]) / len(results), 3),
        "remedy_language_correctness": round(sum(1 for result in results if result["remedy_language_ok"]) / len(results), 3),
        "missing_facts_relevance": round(sum(1 for result in results if result["missing_facts_ok"]) / len(results), 3),
        "raw_enum_visible_count": sum(result["raw_enum_visible_count"] for result in results),
        "hallucinated_section_count": sum(result["hallucinated_section_count"] for result in results),
    }


def _markdown_path(output_path: Path) -> Path:
    return output_path.with_suffix(".md")


def _write_markdown(summary: dict[str, Any], output_path: Path) -> None:
    md_path = _markdown_path(output_path)
    lines = [
        "# NyayaLens Evaluation Summary",
        "",
        f"Scenario file: `{summary['scenario_file']}`",
        f"Scenarios: {summary['scenario_count']}",
        f"Passed: {summary['passed_count']}",
        f"Failed: {summary['failed_count']}",
        "",
        "## Metrics",
    ]
    for key, value in summary["metrics"].items():
        lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
    lines.extend(["", "## Scenario Results", "", "| Scenario | Issue | Domain | Expert | Passed | Notes |", "|---|---|---|---|---|---|"])
    for result in summary["results"]:
        notes = "; ".join(result["failure_reasons"]) if result["failure_reasons"] else ""
        lines.append(
            f"| {result['id']} | {result['issue_type']} | {result['domain']} | "
            f"{result['primary_expert']} | {result['passed']} | {notes} |"
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def _result_for_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    text, filename = _load_text(scenario)
    report = run_analysis(
        text=text,
        filename=filename,
        context=UserContext(**scenario.get("context", {})),
        persist=False,
    )
    view_model = to_report_view_model(report)
    unsafe_refused = bool(report.issue_detected.unsafe_request and report.risk_flags)
    human_facing_text = _human_facing_text(report, view_model)
    remedy_text = " ".join(
        [
            " ".join(report.remedy_plan.steps),
            " ".join(report.remedy_plan.evidence_checklist),
            report.remedy_plan.draft_message or "",
        ]
    )
    forbidden = [phrase.lower() for phrase in scenario.get("forbidden_phrases", [])]
    result = {
        "id": _scenario_id(scenario),
        "name": scenario["name"],
        "document_type": report.extracted_facts.document_type,
        "domain": report.issue_detected.domain,
        "issue_type": report.issue_detected.issue_type,
        "primary_expert": report.expert_route.primary_expert,
        "risk_count": len(report.risk_flags),
        "risk_titles": [risk.title for risk in report.risk_flags],
        "missing_facts": report.missing_facts,
        "disclaimer_exists": "not legal advice" in report.disclaimer.lower(),
        "citations_exist": bool(report.citations),
        "risk_support_coverage": all(
            row.document_citation_ids or row.legal_citation_ids or row.general_info_label
            for row in view_model.risks_table
        ),
        "unsafe_refused": unsafe_refused,
        "verifier_passed": report.verifier.passed,
        "remedy_language_ok": not any(phrase in remedy_text.lower() for phrase in forbidden),
        "missing_facts_ok": all(
            fact in report.missing_facts for fact in scenario.get("expected_missing_facts", [])
        ),
        "retrieved_domains": sorted({source.citation.domain for source in report.retrieved_sources if source.citation.domain}),
        "warnings_text": _flatten_text(
            [
                report.extracted_facts.parser_warnings,
                report.uncertainties,
                view_model.trust_panel.uncertainty_reasons,
                [warning for row in view_model.trust_panel.law_pack_coverage for warning in row.warnings],
            ]
        ),
        "law_pack_statuses": _coverage_statuses(view_model),
        "law_match_acts": _law_match_acts(report),
        "raw_enum_visible_count": _raw_enum_visible_count(human_facing_text),
        "hallucinated_section_count": _hallucinated_section_count(human_facing_text),
        "human_facing_text": human_facing_text,
    }
    result["failure_reasons"] = _scenario_failure_reasons(result, scenario)
    result["passed"] = not result["failure_reasons"]
    result.pop("human_facing_text", None)
    return result


def run_eval(
    scenario_file: str | Path | None = None,
    output: str | Path | None = None,
    *,
    stress: bool = False,
) -> dict[str, Any]:
    ingest_corpus(include_demo=True)
    scenario_path = Path(scenario_file) if scenario_file else (STRESS_SCENARIOS_PATH if stress else SCENARIOS_PATH)
    if not scenario_path.is_absolute():
        scenario_path = ROOT / scenario_path
    output_path = Path(output) if output else (STRESS_OUTPUT_PATH if stress else OUTPUT_PATH)
    if not output_path.is_absolute():
        output_path = ROOT / output_path

    scenarios = json.loads(scenario_path.read_text(encoding="utf-8"))
    results = [_result_for_scenario(scenario) for scenario in scenarios]
    summary = {
        "scenario_file": str(scenario_path.relative_to(ROOT)),
        "scenario_count": len(results),
        "passed_count": sum(1 for result in results if result["passed"]),
        "failed_count": sum(1 for result in results if not result["passed"]),
        "metrics": _metrics(results, scenarios),
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown(summary, output_path)
    print(
        f"Evaluation: {summary['passed_count']}/{summary['scenario_count']} passed. "
        f"Wrote {output_path.relative_to(ROOT)} and {_markdown_path(output_path).relative_to(ROOT)}"
    )
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NyayaLens functional or stress evaluation scenarios.")
    parser.add_argument("--scenario-file", type=Path, default=None, help="Scenario JSON file to run.")
    parser.add_argument("--output", type=Path, default=None, help="JSON summary output path.")
    parser.add_argument("--stress", action="store_true", help="Use stress scenario defaults.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_eval(scenario_file=args.scenario_file, output=args.output, stress=args.stress)
    raise SystemExit(0)
