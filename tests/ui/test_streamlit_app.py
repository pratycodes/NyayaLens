from __future__ import annotations

from pathlib import Path

import pytest


def test_streamlit_app_loads_without_crashing() -> None:
    streamlit_testing = pytest.importorskip("streamlit.testing.v1")
    app_test = streamlit_testing.AppTest.from_file("frontend/streamlit_app.py")

    app = app_test.run(timeout=30)

    assert not app.exception
    assert any("NyayaLens" in title.value for title in app.title)


def test_required_tabs_exist_in_report_ui_source() -> None:
    source = Path("frontend/components/analysis_view.py").read_text(encoding="utf-8")

    for label in [
        "Overview",
        "Risks & Remedies",
        "Document Review",
        "Sources & Citations",
        "Law Cross-Reference",
        "Drafts & Checklist",
        "Evaluation / Trust",
        "Audit / Debug",
    ]:
        assert label in source


def test_main_ui_uses_human_readable_labels_and_hides_debug_from_overview() -> None:
    source = Path("frontend/components/analysis_view.py").read_text(encoding="utf-8")
    overview_source = source.split("def _render_overview", maxsplit=1)[1].split("def _filtered_risks", maxsplit=1)[0]

    assert "display_label" in overview_source
    assert "raw_extracted_clauses" not in overview_source
    assert "debug_payload" not in overview_source


def test_disclaimer_and_demo_mode_warning_are_visible_in_ui_code() -> None:
    app_source = Path("frontend/streamlit_app.py").read_text(encoding="utf-8")
    report_source = Path("frontend/components/analysis_view.py").read_text(encoding="utf-8")

    assert "legal advice" in app_source.lower() or "legal advice" in report_source.lower()
    assert "Offline demo retrieval mode is active" in report_source
