import json
import shutil
from pathlib import Path

import pytest
from backend.app.agents.graph import run_analysis
from backend.app.core.schemas import UserContext
from backend.app.documents.parsers import parse_document
from backend.app.explainability.report_view_model import to_report_view_model
from backend.app.law_packs.coverage import BSA_MISSING_WARNING, build_law_pack_coverage
from backend.app.law_packs.ingest_law_pack import ingest_law_packs
from backend.app.law_packs.law_pack_loader import load_law_sections
from backend.app.law_packs.manifest import load_law_pack_manifest
from backend.app.law_packs.official_source_metadata import infer_law_metadata
from backend.app.law_packs.validation import validate_inferred_law_file
from backend.tests.test_freelance_service_agreement import FREELANCE_AGREEMENT
from scripts.generate_section_law_packs import extract_sections


def _coverage_by_act_id():
    return {row.act_id: row for row in build_law_pack_coverage()}


def test_manifest_loads_expected_law_packs() -> None:
    manifest = load_law_pack_manifest()
    act_ids = {entry.act_id for entry in manifest.entries}

    assert "bns_2023" in act_ids
    assert "bnss_2023" in act_ids
    assert "bsa_2023" in act_ids
    assert "indian_contract_act_1872" in act_ids
    assert "maharashtra_rent_control_act_1999" in act_ids
    assert "karnataka_rent_act_1999" in act_ids
    assert "delhi_rent_control_act_1958" in act_ids
    assert "punjab_rent_act_1995" in act_ids
    assert "up_urban_premises_tenancy_act_2021" in act_ids
    assert "west_bengal_premises_tenancy_act_1997" in act_ids
    assert "rajasthan_rent_control_act_2001" in act_ids


def test_bsa_official_is_loaded() -> None:
    bsa = _coverage_by_act_id()["bsa_2023"]

    assert bsa.status == "loaded_official"
    assert BSA_MISSING_WARNING not in bsa.warnings
    assert bsa.required_for_official_mode is True


def test_mismatched_bsa_file_rejected_if_parses_as_ipc(tmp_path: Path) -> None:
    root = tmp_path / "official"
    root.mkdir()
    manifest = {
        "version": "1.0",
        "entries": [
            {
                "act_id": "bsa_2023",
                "expected_title": "Bharatiya Sakshya Adhiniyam, 2023",
                "expected_act_no": "47 of 2023",
                "domain": "criminal_screening",
                "jurisdiction": "India",
                "historical": False,
                "effective_from": "2024-07-01",
                "effective_to": None,
                "required_for_official_mode": True,
                "allowed_aliases": ["THE BHARATIYA SAKSHYA ADHINIYAM, 2023"],
                "expected_source_files": ["250882_english_01042024.pdf"],
                "source_authority": "Ministry of Home Affairs",
                "notes": "Synthetic mismatch fixture.",
            }
        ],
    }
    (root / "law_pack_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    path = root / "criminal" / "250882_english_01042024.pdf"
    text = "THE INDIAN PENAL CODE\nARRANGEMENT OF SECTIONS"
    metadata = infer_law_metadata(path.stem, "criminal", text)

    result = validate_inferred_law_file(path, "criminal", text, metadata, root=root)

    assert result.status == "rejected_metadata_mismatch"
    assert result.expected_act_id == "bsa_2023"
    assert result.parsed_title == "Indian Penal Code, 1860"


def test_ipc_reference_inside_other_act_does_not_change_act_metadata() -> None:
    text = """
    THE INDIAN CONTRACT ACT, 1872
    A later clause mentions the Indian Penal Code for a narrow cross-reference.
    """

    metadata = infer_law_metadata("A187209", "contract", text)

    assert metadata.act_name == "Indian Contract Act, 1872"
    assert metadata.domain == "contract_payment"


def test_coverage_report_contains_bns_bnss_bsa() -> None:
    coverage = _coverage_by_act_id()

    assert coverage["bns_2023"].status == "loaded_official"
    assert coverage["bnss_2023"].status == "loaded_official"
    assert coverage["bsa_2023"].status == "loaded_official"


def test_trust_panel_displays_law_pack_coverage() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="demo_freelance_agreement.txt",
        context=UserContext(user_role="freelancer", query="I have not been paid."),
        persist=False,
    )
    view_model = to_report_view_model(report)

    assert view_model.trust_panel.law_pack_coverage
    assert any(row.act_id == "bsa_2023" for row in view_model.trust_panel.law_pack_coverage)


def test_current_criminal_law_has_no_bsa_missing_warning_when_loaded() -> None:
    report = run_analysis(
        text="The counterparty used a forged invoice.",
        filename="plain_text.txt",
        context=UserContext(query="The counterparty used a forged invoice.", dispute_date="2026-01-01"),
        persist=False,
    )
    view_model = to_report_view_model(report)

    assert BSA_MISSING_WARNING not in view_model.trust_panel.uncertainty_reasons


def test_historical_ipc_marked_historical() -> None:
    ipc = _coverage_by_act_id()["ipc_1860"]

    assert ipc.historical is True
    assert ipc.required_for_official_mode is False
    assert ipc.status == "historical_loaded"
    assert "data/raw/official/criminal/THE-INDIAN-PENAL-CODE-1860.pdf" in ipc.source_files


def test_karnataka_rent_act_loaded_official() -> None:
    karnataka = _coverage_by_act_id()["karnataka_rent_act_1999"]

    assert karnataka.status == "loaded_official"
    assert karnataka.chunks_count > 20
    assert "data/raw/official/tenancy/34 of 2001 (E).pdf" in karnataka.source_files


def test_requested_state_tenancy_packs_loaded_official() -> None:
    coverage = _coverage_by_act_id()
    expected = {
        "delhi_rent_control_act_1958": "Delhi Rent Control Act, 1958",
        "punjab_rent_act_1995": "Punjab Rent Act, 1995",
        "up_urban_premises_tenancy_act_2021": "Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021",
        "west_bengal_premises_tenancy_act_1997": "West Bengal Premises Tenancy Act, 1997",
        "rajasthan_rent_control_act_2001": "Rajasthan Rent Control Act, 2001",
    }

    for act_id, title in expected.items():
        row = coverage[act_id]
        assert row.expected_title == title
        assert row.status == "loaded_official"
        assert row.chunks_count > 10


def test_bihar_limited_public_premises_loaded_and_private_pack_marked_missing() -> None:
    coverage = _coverage_by_act_id()
    private_bihar = coverage["bihar_buildings_lease_rent_eviction_control_act_1982"]
    public_premises_bihar = coverage["bihar_government_premises_rent_recovery_eviction_act_1956"]

    assert private_bihar.status == "missing_official"
    assert private_bihar.required_for_official_mode is True
    assert any("Official pack missing" in warning for warning in private_bihar.warnings)
    assert public_premises_bihar.status == "loaded_official"
    assert public_premises_bihar.required_for_official_mode is False
    assert public_premises_bihar.chunks_count > 5


def test_up_tenancy_ocr_derivative_generates_section_pack() -> None:
    up = _coverage_by_act_id()["up_urban_premises_tenancy_act_2021"]

    assert up.status == "loaded_official"
    assert "data/raw/official/tenancy/up_urban_premises_tenancy_act_2021_ocr.txt" in up.source_files
    assert up.chunks_count > 20


def test_garbled_pdf_uses_pdftotext_fallback_for_karnataka_rent_act() -> None:
    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext is optional and not installed in this environment.")
    parsed = parse_document(Path("data/raw/official/tenancy/34 of 2001 (E).pdf"))

    assert "THE KARNATAKA RENT ACT, 1999" in parsed.text
    assert any("pdftotext fallback" in warning for warning in parsed.warnings)


def test_generated_section_law_packs_loaded() -> None:
    sections = load_law_sections()
    bns_sections = [
        section
        for section in sections
        if section.act_id == "bns_2023" and section.section_number != "full_act"
    ]
    contract_sections = [
        section
        for section in sections
        if section.act_id == "indian_contract_act_1872" and section.section_number != "full_act"
    ]

    assert len(bns_sections) > 100
    assert len(contract_sections) > 20
    assert all(section.corpus_mode == "official" for section in bns_sections[:5])


def test_section_extractor_keeps_longest_section_body() -> None:
    sections = extract_sections(
        """
        1. Short title.
        2. Definitions.
        1. Short title, extent and commencement.
        This section has a longer body and should be selected over the arrangement entry.
        It includes actual statutory text rather than a table of contents line.
        2. Definitions.
        Definitions section body with enough text to survive the section-length filter.
        The exact legal effect is not inferred by this parser.
        This additional sentence makes the fixture closer to an extracted statutory section.
        It should be long enough to be retained as a body section rather than a table entry.
        """
    )

    assert [section["section_number"] for section in sections] == ["1", "2"]
    assert "longer body" in sections[0]["text"]


def test_ingestion_continues_when_optional_official_pack_missing() -> None:
    sections = ingest_law_packs()
    coverage = _coverage_by_act_id()

    assert sections
    assert coverage["ipc_1860"].required_for_official_mode is False
