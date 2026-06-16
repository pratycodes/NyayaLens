from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.config import ROOT_DIR
from backend.app.law_packs.law_pack_loader import load_law_sections
from backend.app.law_packs.manifest import LawPackManifestEntry, load_law_pack_manifest
from backend.app.law_packs.schemas import LawSection
from backend.app.law_packs.validation import LawPackFileValidation, validate_law_pack_files

CoverageStatus = Literal[
    "loaded_official",
    "loaded_demo",
    "missing_official",
    "rejected_metadata_mismatch",
    "historical_loaded",
]

BSA_MISSING_WARNING = (
    "Official Bharatiya Sakshya Adhiniyam pack is missing; "
    "evidence-law cross-reference may be incomplete."
)


class LawPackCoverage(BaseModel):
    act_id: str
    expected_title: str
    status: CoverageStatus
    chunks_count: int
    source_files: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    required_for_official_mode: bool
    corpus_mode: str
    historical: bool = False


def _norm(value: str | None) -> str:
    return " ".join((value or "").lower().replace(",", " ").split())


def _matches_entry(section: LawSection, entry: LawPackManifestEntry) -> bool:
    aliases = {_norm(entry.expected_title), *{_norm(alias) for alias in entry.allowed_aliases}}
    return section.act_id == entry.act_id or _norm(section.act_name) in aliases


def _rejections_for_entry(
    entry: LawPackManifestEntry,
    validations: list[LawPackFileValidation],
) -> list[LawPackFileValidation]:
    return [
        item
        for item in validations
        if item.status == "rejected_metadata_mismatch"
        and (item.expected_act_id == entry.act_id or _norm(item.expected_title) == _norm(entry.expected_title))
    ]


def _status_for_entry(
    entry: LawPackManifestEntry,
    official: list[LawSection],
    demo: list[LawSection],
    rejected: list[LawPackFileValidation],
) -> CoverageStatus:
    if official:
        return "historical_loaded" if entry.historical else "loaded_official"
    if rejected:
        return "rejected_metadata_mismatch"
    if demo:
        return "loaded_demo"
    return "missing_official"


def _warnings_for_entry(
    entry: LawPackManifestEntry,
    status: CoverageStatus,
    rejected: list[LawPackFileValidation],
    demo: list[LawSection],
) -> list[str]:
    warnings: list[str] = []
    for item in rejected:
        if item.warnings:
            warnings.extend(item.warnings)
        warnings.append(
            f"Rejected {item.source_file}: expected {item.expected_title}, parsed {item.parsed_title}."
        )
    if entry.required_for_official_mode and status in {
        "missing_official",
        "loaded_demo",
        "rejected_metadata_mismatch",
    }:
        warnings.append(f"Official pack missing for required law pack: {entry.expected_title}.")
    if demo and status != "loaded_official":
        warnings.append("Demo placeholder is available but does not replace an official source.")
    if entry.act_id == "bsa_2023" and status != "loaded_official":
        warnings.append(BSA_MISSING_WARNING)
    return sorted(set(warnings))


def build_law_pack_coverage(root: Path | None = None) -> list[LawPackCoverage]:
    manifest = load_law_pack_manifest(root)
    validations = validate_law_pack_files(root).files
    sections = load_law_sections(root)
    rows: list[LawPackCoverage] = []
    for entry in manifest.entries:
        matching_sections = [section for section in sections if _matches_entry(section, entry)]
        official = [section for section in matching_sections if section.corpus_mode == "official"]
        demo = [section for section in matching_sections if section.corpus_mode == "demo"]
        rejected = _rejections_for_entry(entry, validations)
        status = _status_for_entry(entry, official, demo, rejected)
        source_files = sorted(
            {
                *(section.source_file or section.act_id for section in matching_sections),
                *(item.source_file for item in rejected),
            }
        )
        mode_parts = []
        if official:
            mode_parts.append("official")
        if demo:
            mode_parts.append("demo")
        if rejected:
            mode_parts.append("rejected")
        rows.append(
            LawPackCoverage(
                act_id=entry.act_id,
                expected_title=entry.expected_title,
                status=status,
                chunks_count=len(matching_sections),
                source_files=source_files,
                warnings=_warnings_for_entry(entry, status, rejected, demo),
                required_for_official_mode=entry.required_for_official_mode,
                corpus_mode="/".join(mode_parts) if mode_parts else "missing",
                historical=entry.historical,
            )
        )
    return rows


def write_law_pack_coverage_report(
    output_path: Path | None = None,
    *,
    root: Path | None = None,
) -> Path:
    path = output_path or ROOT_DIR / "demo_outputs" / "law_pack_coverage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [row.model_dump(mode="json") for row in build_law_pack_coverage(root)]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
