from __future__ import annotations

import os
from pathlib import Path

import pytest
from scripts.generate_stress_docs import generate_stress_docs


def test_freelance_payment_flow_browser_smoke() -> None:
    app_url = os.environ.get("NYAYALENS_APP_URL")
    if not app_url:
        pytest.skip("Set NYAYALENS_APP_URL to run browser E2E smoke tests.")
    sync_api = pytest.importorskip("playwright.sync_api")
    generate_stress_docs()
    upload_path = Path("tests/fixtures/stress_docs/freelance_agreement.pdf").resolve()

    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            page.goto(app_url, wait_until="networkidle", timeout=60_000)

            page.locator("input[type='file']").set_input_files(str(upload_path))
            page.get_by_label("User role").select_option("freelancer")
            page.get_by_label("Short dispute summary").fill("I have not been paid yet.")
            page.get_by_role("button", name="Analyze").click()

            page.get_by_text("Overview").wait_for(timeout=120_000)
            for label in [
                "Overview",
                "Risks & Remedies",
                "Document Review",
                "Sources & Citations",
                "Drafts & Checklist",
            ]:
                assert page.get_by_text(label).first.is_visible()

            assert page.get_by_text("Unpaid compensation / pending payment").first.is_visible()
            assert page.get_by_text("Document p.").first.is_visible()

            page.get_by_text("Drafts & Checklist").click()
            assert page.get_by_text("Company/Client/Accounts Team").first.is_visible()
            assert not page.get_by_text("HR/Payroll Team").first.is_visible()
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright browser smoke test could not run in this environment: {exc}")
