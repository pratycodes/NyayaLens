from __future__ import annotations

import json
import re
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.config import ROOT_DIR
from backend.app.documents.parsers import parse_document
from backend.app.law_packs.manifest import LawPackManifestEntry, load_law_pack_manifest
from backend.app.law_packs.official_source_metadata import InferredLawMetadata, infer_law_metadata
from backend.app.law_packs.registry import (
    ensure_law_pack_folders,
    law_pack_folders,
    official_law_pack_root,
)

VALIDATION_STATUSES = Literal[
    "accepted_official",
    "accepted_demo",
    "accepted_unmanifested_demo",
    "rejected_metadata_mismatch",
]


class LawPackFileValidation(BaseModel):
    source_file: str
    status: VALIDATION_STATUSES
    expected_act_id: str | None = None
    expected_title: str | None = None
    expected_act_no: str | None = None
    parsed_act_id: str | None = None
    parsed_title: str | None = None
    parsed_act_no: str | None = None
    expected_domain: str | None = None
    parsed_domain: str | None = None
    expected_historical: bool | None = None
    parsed_historical: bool | None = None
    warnings: list[str] = Field(default_factory=list)


class LawPackValidationReport(BaseModel):
    files: list[LawPackFileValidation] = Field(default_factory=list)

    @property
    def rejected_files(self) -> list[LawPackFileValidation]:
        return [item for item in self.files if item.status == "rejected_metadata_mismatch"]


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT_DIR))
    except ValueError:
        return path.name


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _parse_act_no(text: str) -> str | None:
    sample = text[:120000]
    act_number = r"([A-Z]+|\d+)"
    patterns = [
        rf"\bACT\s+NO\.?\s+{act_number}\s+OF\s+(\d{{4}})",
        rf"\bNO\.?\s+{act_number}\s+OF\s+(\d{{4}})",
        rf"\bMAH\.\s+ACT\s+NO\.?\s+{act_number}\s+OF\s+(\d{{4}})",
        rf"\bBIHAR\s+ACT\s+{act_number}\s+OF\s+(\d{{4}})",
        rf"\bPUNJAB\s+ACT\s+{act_number}\s+OF\s+(\d{{4}})",
        rf"\bU\.?\s*P\.?\s+ACT\s+NO\.?\s+{act_number}\s+OF\s+(\d{{4}})",
        rf"\bWEST\s+BENGAL\s+ACT\s+{act_number}\s+OF\s+(\d{{4}})",
        rf"\bWEST\s+BEN\.\s+ACT\s+{act_number}\s+OF\s+(\d{{4}})",
        rf"\bRAJASTHAN\s+ACT\s+{act_number}\s+OF\s+(\d{{4}})",
    ]
    for pattern in patterns:
        match = re.search(pattern, sample, flags=re.IGNORECASE)
        if match:
            prefix = sample[max(0, match.start() - 40) : match.start()].upper()
            if "CENTRAL ACT" in prefix:
                continue
            number = match.group(1)
            formatted_number = str(int(number)) if number.isdigit() else number.upper()
            return f"{formatted_number} of {match.group(2)}"
    return None


def _is_historical(metadata: InferredLawMetadata) -> bool:
    return bool(metadata.effective_to and metadata.effective_to <= "2024-06-30")


def _filename_matches(path: Path, entry: LawPackManifestEntry) -> bool:
    filenames = {_normalize(item) for item in entry.expected_source_files}
    return _normalize(path.name) in filenames or _normalize(_display_path(path)) in filenames


def _title_matches(metadata: InferredLawMetadata, entry: LawPackManifestEntry) -> bool:
    parsed = _normalize(metadata.act_name)
    expected_titles = {_normalize(entry.expected_title), *{_normalize(alias) for alias in entry.allowed_aliases}}
    return parsed in expected_titles


def _entry_for_file(path: Path, metadata: InferredLawMetadata, root: Path | None) -> LawPackManifestEntry | None:
    manifest = load_law_pack_manifest(root)
    for entry in manifest.entries:
        if _filename_matches(path, entry):
            return entry
    for entry in manifest.entries:
        if metadata.act_id == entry.act_id or _title_matches(metadata, entry):
            return entry
    return None


def validate_inferred_law_file(
    path: Path,
    folder_domain: str,
    text: str,
    metadata: InferredLawMetadata,
    *,
    root: Path | None = None,
) -> LawPackFileValidation:
    corpus_mode = "official" if "official" in path.parts and "demo" not in path.name.lower() else "demo"
    parsed_act_no = _parse_act_no(text)
    if corpus_mode == "demo":
        return LawPackFileValidation(
            source_file=_display_path(path),
            status="accepted_demo",
            parsed_act_id=metadata.act_id,
            parsed_title=metadata.act_name,
            parsed_act_no=parsed_act_no,
            parsed_domain=metadata.domain,
            parsed_historical=_is_historical(metadata),
        )

    entry = _entry_for_file(path, metadata, root)
    if entry is None:
        return LawPackFileValidation(
            source_file=_display_path(path),
            status="rejected_metadata_mismatch",
            parsed_act_id=metadata.act_id,
            parsed_title=metadata.act_name,
            parsed_act_no=parsed_act_no,
            parsed_domain=metadata.domain,
            parsed_historical=_is_historical(metadata),
            warnings=[
                "Official file is not represented in law_pack_manifest.json and was rejected.",
                f"Folder domain was {folder_domain}.",
            ],
        )

    if entry.expected_act_no is None:
        parsed_act_no = None

    warnings: list[str] = []
    if not _title_matches(metadata, entry):
        warnings.append(
            f"Expected title '{entry.expected_title}' but parsed '{metadata.act_name}'."
        )
    if entry.expected_act_no and parsed_act_no and _normalize(entry.expected_act_no) != _normalize(parsed_act_no):
        warnings.append(
            f"Expected Act No. '{entry.expected_act_no}' but parsed '{parsed_act_no}'."
        )
    if _normalize(entry.domain) != _normalize(metadata.domain):
        warnings.append(f"Expected domain '{entry.domain}' but parsed '{metadata.domain}'.")
    parsed_historical = _is_historical(metadata)
    if entry.historical != parsed_historical:
        warnings.append(
            f"Expected historical={entry.historical} but parsed historical={parsed_historical}."
        )

    return LawPackFileValidation(
        source_file=_display_path(path),
        status="rejected_metadata_mismatch" if warnings else "accepted_official",
        expected_act_id=entry.act_id,
        expected_title=entry.expected_title,
        expected_act_no=entry.expected_act_no,
        parsed_act_id=metadata.act_id,
        parsed_title=metadata.act_name,
        parsed_act_no=parsed_act_no,
        expected_domain=entry.domain,
        parsed_domain=metadata.domain,
        expected_historical=entry.historical,
        parsed_historical=parsed_historical,
        warnings=warnings,
    )


def _validation_root_key(root: Path | None) -> str:
    return str(root.resolve()) if root else ""


@lru_cache(maxsize=4)
def _validate_law_pack_files_cached(root_key: str) -> tuple[LawPackFileValidation, ...]:
    root = Path(root_key) if root_key else None
    ensure_law_pack_folders(root)
    validations: list[LawPackFileValidation] = []
    for folder in law_pack_folders(root):
        folder_domain = folder.name
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".txt", ".pdf", ".docx"}:
                continue
            parsed = parse_document(path)
            metadata = infer_law_metadata(path.stem, folder_domain, parsed.text)
            validations.append(
                validate_inferred_law_file(
                    path,
                    folder_domain,
                    parsed.text,
                    metadata,
                    root=root,
                )
            )
    return tuple(validations)


def validate_law_pack_files(root: Path | None = None) -> LawPackValidationReport:
    return LawPackValidationReport(files=list(_validate_law_pack_files_cached(_validation_root_key(root))))


def write_law_pack_validation_report(
    output_path: Path | None = None,
    *,
    root: Path | None = None,
) -> Path:
    path = output_path or ROOT_DIR / "demo_outputs" / "law_pack_validation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    report = validate_law_pack_files(root)
    payload = [item.model_dump(mode="json") for item in report.files]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def quarantine_mismatched_files(root: Path | None = None) -> list[str]:
    base = root or official_law_pack_root()
    quarantine_dir = base / "_quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for item in validate_law_pack_files(root).rejected_files:
        source = ROOT_DIR / item.source_file if not Path(item.source_file).is_absolute() else Path(item.source_file)
        if not source.exists():
            continue
        destination = quarantine_dir / source.name
        if destination.exists():
            destination = quarantine_dir / f"{source.stem}-rejected{source.suffix}"
        shutil.move(str(source), str(destination))
        moved.append(_display_path(destination))
    _validate_law_pack_files_cached.cache_clear()
    return moved
