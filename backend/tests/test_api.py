from __future__ import annotations

from pathlib import Path

from backend.app.main import app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


def test_health_api() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_api_with_sample_text() -> None:
    client = TestClient(app)
    text = (ROOT / "data/raw/sample_uploads/sample_employment_contract.txt").read_text()
    response = client.post(
        "/analyze",
        json={
            "text": text,
            "filename": "sample_employment_contract.txt",
            "context": {
                "city": "Bengaluru",
                "state": "Karnataka",
                "user_role": "employee",
                "selected_dispute_type": "auto-detect",
                "query": "Company is withholding salary and asking for bond recovery.",
            },
        },
    )
    assert response.status_code == 200, response.text
    report = response.json()["report"]
    assert report["issue_detected"]["domain"] == "employment"
    assert report["risk_flags"]
    assert report["citations"]
    assert "not legal advice" in report["disclaimer"].lower()


def test_upload_rejects_large_file() -> None:
    client = TestClient(app)
    oversized = b"x" * (11 * 1024 * 1024)
    response = client.post(
        "/upload",
        files={"file": ("large.txt", oversized, "text/plain")},
    )
    assert response.status_code == 413


def test_cors_rejects_unconfigured_origin() -> None:
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") != "http://evil.example"
