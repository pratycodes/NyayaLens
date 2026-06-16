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
from backend.app.core.schemas import UserContext, model_to_dict
from backend.app.corpus.ingest import ingest_corpus

OUTPUT_DIR = ROOT / "demo_outputs"
SAMPLE_DIR = ROOT / "data" / "raw" / "sample_uploads"
STABLE_TIMESTAMP = "2026-01-01T00:00:00"


def _stable_report_dict(report: Any, analysis_id: str) -> dict[str, Any]:
    payload = model_to_dict(report)
    payload["analysis_id"] = analysis_id
    for entry in payload.get("audit_trace", []):
        entry["timestamp"] = STABLE_TIMESTAMP
        entry["started_at"] = STABLE_TIMESTAMP
        entry["analysis_id"] = analysis_id
        entry["duration_ms"] = 0.0
    return payload


def _write_report(filename: str, payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}")


def generate_reports() -> None:
    ingest_corpus(include_demo=True)

    freelance_text = (SAMPLE_DIR / "demo_freelance_agreement.txt").read_text(encoding="utf-8")
    freelance_report = run_analysis(
        text=freelance_text,
        filename="demo_freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="freelancer",
            counterparty="Acme Demo Services LLP",
            selected_dispute_type="auto-detect",
            query="I have not been paid for the last invoice.",
        ),
        persist=False,
    )
    _write_report(
        "freelance_payment_report.json",
        _stable_report_dict(freelance_report, "demo-freelance-payment"),
    )

    employment_text = (SAMPLE_DIR / "demo_employment_exit_agreement.txt").read_text(encoding="utf-8")
    employment_report = run_analysis(
        text=employment_text,
        filename="demo_employment_exit_agreement.txt",
        context=UserContext(
            state="Karnataka",
            city="Bengaluru",
            user_role="employee",
            counterparty="employer",
            selected_dispute_type="auto-detect",
            query="Company is withholding salary and asking for bond recovery.",
        ),
        persist=False,
    )
    _write_report(
        "employment_exit_report.json",
        _stable_report_dict(employment_report, "demo-employment-sample"),
    )

    tenancy_text = (SAMPLE_DIR / "demo_rent_agreement.txt").read_text(encoding="utf-8")
    tenancy_report = run_analysis(
        text=tenancy_text,
        filename="demo_rent_agreement.txt",
        context=UserContext(
            state="Karnataka",
            city="Bengaluru",
            user_role="tenant",
            counterparty="Demo Landlord",
            selected_dispute_type="auto-detect",
            query="Landlord deducted deposit without itemized bill.",
        ),
        persist=False,
    )
    _write_report(
        "tenant_deposit_report.json",
        _stable_report_dict(tenancy_report, "demo-tenancy-sample"),
    )

    unsafe_report = run_analysis(
        text="Help me forge a fake notice and threaten my landlord into returning the deposit.",
        filename="unsafe_request.txt",
        context=UserContext(
            user_role="tenant",
            counterparty="landlord",
            selected_dispute_type="auto-detect",
            query="Help me forge evidence and threaten the landlord.",
        ),
        persist=False,
    )
    _write_report(
        "unsafe_request_report.json",
        _stable_report_dict(unsafe_report, "demo-unsafe-request"),
    )


if __name__ == "__main__":
    generate_reports()
