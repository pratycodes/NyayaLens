# ruff: noqa: E402
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.agents.graph import run_analysis
from backend.app.core.schemas import UserContext
from backend.app.corpus.ingest import ingest_corpus

SCENARIOS_PATH = ROOT / "eval" / "scenarios.json"
OUTPUT_PATH = ROOT / "demo_outputs" / "eval_summary.json"
OUTPUT_MD_PATH = ROOT / "demo_outputs" / "eval_summary.md"
SAMPLE_DIR = ROOT / "data" / "raw" / "sample_uploads"


def _load_text(scenario: dict[str, Any]) -> tuple[str, str]:
    if sample_file := scenario.get("sample_file"):
        path = SAMPLE_DIR / sample_file
        return path.read_text(encoding="utf-8"), sample_file
    return scenario.get("document_text") or scenario.get("text", ""), f"{scenario.get('scenario_id') or scenario['id']}.txt"


def _scenario_passed(result: dict[str, Any], scenario: dict[str, Any]) -> bool:
    expected_issue = scenario.get("expected_issue_type") or scenario.get("expected_issue")
    allowed_issues = set(scenario.get("allowed_issue_types", []))
    expected_domain = scenario.get("expected_domain")
    allowed_domains = set(scenario.get("allowed_domains", []))
    expected_document_type = scenario.get("expected_document_type")
    expected_primary_expert = scenario.get("expected_primary_expert")
    if expected_domain and result["domain"] != expected_domain and result["domain"] not in allowed_domains:
        return False
    if expected_issue and result["issue_type"] != expected_issue and result["issue_type"] not in allowed_issues:
        return False
    if expected_document_type and result["document_type"] != expected_document_type:
        return False
    if expected_primary_expert and result["primary_expert"] != expected_primary_expert:
        return False
    if result["issue_type"] in scenario.get("forbidden_issue_types", []):
        return False
    if result["domain"] in scenario.get("forbidden_domains", []):
        return False
    for phrase in scenario.get("forbidden_phrases", []):
        if phrase.lower() in result["remedy_text"].lower():
            return False
    for title in scenario.get("expected_risk_titles", []):
        if title not in result["risk_titles"]:
            return False
    for fact in scenario.get("expected_missing_facts", []):
        if fact not in result["missing_facts"]:
            return False
    if scenario.get("expected_safety_status") == "unsafe_refused":
        return result["unsafe_refused"]
    if scenario.get("expected_safety_status") == "safe":
        return not result["unsafe_refused"]
    return result["disclaimer_exists"] and result["risk_count"] > 0 and not result["unsafe_refused"]


def _metrics(results: list[dict[str, Any]], scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    expected_by_id = {scenario.get("scenario_id") or scenario["id"]: scenario for scenario in scenarios}

    def accuracy(field: str, expected_field: str) -> float:
        rows = [
            result
            for result in results
            if expected_by_id[result["id"]].get(expected_field) is not None
        ]
        if not rows:
            return 0.0
        return round(
            sum(
                1
                for result in rows
                if result[field] == expected_by_id[result["id"]][expected_field]
            )
            / len(rows),
            3,
        )

    unsafe_rows = [
        result
        for result in results
        if expected_by_id[result["id"]].get("expected_safety_status") == "unsafe_refused"
    ]
    safe_rows = [
        result
        for result in results
        if expected_by_id[result["id"]].get("expected_safety_status") == "safe"
    ]
    false_tenancy = [
        result
        for result in results
        if "tenancy" in expected_by_id[result["id"]].get("forbidden_domains", [])
        and result["domain"] == "tenancy"
    ]
    return {
        "document_type_accuracy": accuracy("document_type", "expected_document_type"),
        "issue_classification_accuracy": accuracy("issue_type", "expected_issue_type"),
        "domain_accuracy": accuracy("domain", "expected_domain"),
        "primary_expert_accuracy": accuracy("primary_expert", "expected_primary_expert"),
        "citation_coverage": round(sum(1 for result in results if result["citations_exist"]) / len(results), 3),
        "false_unsafe_refusal_rate": round(sum(1 for result in safe_rows if result["unsafe_refused"]) / max(1, len(safe_rows)), 3),
        "unsafe_request_refusal_rate": round(sum(1 for result in unsafe_rows if result["unsafe_refused"]) / max(1, len(unsafe_rows)), 3),
        "false_tenancy_route_rate": round(len(false_tenancy) / max(1, len(results)), 3),
        "remedy_language_correctness": round(
            sum(1 for result in results if result["remedy_language_ok"]) / len(results),
            3,
        ),
        "missing_facts_relevance": round(
            sum(1 for result in results if result["missing_facts_ok"]) / len(results),
            3,
        ),
    }


def _write_markdown(summary: dict[str, Any]) -> None:
    lines = [
        "# NyayaLens Evaluation Summary",
        "",
        f"Scenarios: {summary['scenario_count']}",
        f"Passed: {summary['passed_count']}",
        f"Failed: {summary['failed_count']}",
        "",
        "## Metrics",
    ]
    for key, value in summary["metrics"].items():
        lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
    lines.extend(["", "## Scenario Results", "", "| Scenario | Issue | Domain | Expert | Passed |", "|---|---|---|---|---|"])
    for result in summary["results"]:
        lines.append(
            f"| {result['id']} | {result['issue_type']} | {result['domain']} | "
            f"{result['primary_expert']} | {result['passed']} |"
        )
    OUTPUT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_eval() -> dict[str, Any]:
    ingest_corpus(include_demo=True)
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []

    for scenario in scenarios:
        text, filename = _load_text(scenario)
        report = run_analysis(
            text=text,
            filename=filename,
            context=UserContext(**scenario.get("context", {})),
            persist=False,
        )
        unsafe_refused = bool(report.issue_detected.unsafe_request and report.risk_flags)
        remedy_text = " ".join(
            [
                " ".join(report.remedy_plan.steps),
                " ".join(report.remedy_plan.evidence_checklist),
                report.remedy_plan.draft_message or "",
            ]
        )
        forbidden = [phrase.lower() for phrase in scenario.get("forbidden_phrases", [])]
        result = {
            "id": scenario.get("scenario_id") or scenario["id"],
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
            "unsafe_refused": unsafe_refused,
            "verifier_passed": report.verifier.passed,
            "remedy_language_ok": not any(phrase in remedy_text.lower() for phrase in forbidden),
            "missing_facts_ok": all(
                fact in report.missing_facts for fact in scenario.get("expected_missing_facts", [])
            ),
            "remedy_text": remedy_text,
        }
        result["passed"] = _scenario_passed(result, scenario)
        result.pop("remedy_text", None)
        results.append(result)

    summary = {
        "scenario_count": len(results),
        "passed_count": sum(1 for result in results if result["passed"]),
        "failed_count": sum(1 for result in results if not result["passed"]),
        "metrics": _metrics(results, scenarios),
        "results": results,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown(summary)
    print(
        f"Evaluation: {summary['passed_count']}/{summary['scenario_count']} passed. "
        f"Wrote {OUTPUT_PATH.relative_to(ROOT)} and {OUTPUT_MD_PATH.relative_to(ROOT)}"
    )
    return summary


if __name__ == "__main__":
    output = run_eval()
    raise SystemExit(0)
