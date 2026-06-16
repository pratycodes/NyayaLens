from __future__ import annotations

import json
from pathlib import Path

from locust import HttpUser, between, task

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "stress_docs"


class NyayaLensApiUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def health(self) -> None:
        self.client.get("/health", name="GET /health")

    @task(2)
    def analyze_freelance_text(self) -> None:
        text = (FIXTURE_DIR / "freelance_agreement.txt").read_text(encoding="utf-8")
        payload = {
            "text": text,
            "filename": "freelance_agreement.txt",
            "context": {
                "state": "Maharashtra",
                "city": "Mumbai",
                "user_role": "freelancer",
                "selected_dispute_type": "auto-detect",
                "query": "I have not been paid yet.",
            },
        }
        self.client.post(
            "/analyze",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            name="POST /analyze freelance",
        )

    @task(2)
    def analyze_tenancy_text(self) -> None:
        text = (FIXTURE_DIR / "rent_agreement.txt").read_text(encoding="utf-8")
        payload = {
            "text": text,
            "filename": "rent_agreement.txt",
            "context": {
                "state": "Karnataka",
                "city": "Bengaluru",
                "user_role": "tenant",
                "selected_dispute_type": "auto-detect",
                "query": "Landlord deducted my security deposit without itemized bill.",
            },
        }
        self.client.post(
            "/analyze",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            name="POST /analyze tenancy",
        )

    @task(1)
    def upload_freelance_pdf_then_analyze(self) -> None:
        pdf_path = FIXTURE_DIR / "freelance_agreement.pdf"
        with pdf_path.open("rb") as file:
            response = self.client.post(
                "/upload",
                files={"file": ("freelance_agreement.pdf", file, "application/pdf")},
                name="POST /upload PDF",
            )
        if response.status_code != 200:
            return
        upload_id = response.json().get("upload_id")
        payload = {
            "upload_id": upload_id,
            "context": {
                "state": "Maharashtra",
                "city": "Mumbai",
                "user_role": "freelancer",
                "selected_dispute_type": "auto-detect",
                "query": "I have not been paid yet.",
            },
        }
        self.client.post(
            "/analyze",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            name="POST /analyze uploaded PDF",
        )
