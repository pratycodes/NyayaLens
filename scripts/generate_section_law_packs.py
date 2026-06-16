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

from backend.app.documents.parsers import parse_document
from backend.app.law_packs.law_pack_loader import clear_law_pack_cache
from backend.app.law_packs.official_source_metadata import InferredLawMetadata, infer_law_metadata
from backend.app.law_packs.registry import ensure_law_pack_folders, law_pack_folders
from backend.app.law_packs.validation import validate_inferred_law_file

SUPPORTED_SOURCE_SUFFIXES = {".pdf", ".txt", ".docx"}
SECTION_START_RE = re.compile(
    r"(?m)^\s*(?P<number>\d+[A-Z]?)\.\s+(?P<title>[^\n]{3,180})$"
)


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return path.name


def _clean_title(value: str) -> str:
    title = " ".join(value.replace("_", " ").split())
    title = re.sub(r"\s+", " ", title)
    return title.strip(" .-")


def _section_candidates(text: str) -> list[dict[str, Any]]:
    starts = list(SECTION_START_RE.finditer(text))
    candidates: list[dict[str, Any]] = []
    for index, match in enumerate(starts):
        start = match.start()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        raw_text = text[start:end].strip()
        if len(raw_text) < 180:
            continue
        title = _clean_title(match.group("title"))
        # Skip table-of-contents fragments where the title is mostly punctuation or digits.
        if len(re.sub(r"[^A-Za-z]", "", title)) < 4:
            continue
        candidates.append(
            {
                "section_number": match.group("number"),
                "section_title": title[:160],
                "text": raw_text,
            }
        )
    return candidates


def extract_sections(text: str) -> list[dict[str, Any]]:
    best_by_number: dict[str, dict[str, Any]] = {}
    for candidate in _section_candidates(text):
        number = candidate["section_number"]
        previous = best_by_number.get(number)
        if previous is None or len(candidate["text"]) > len(previous["text"]):
            best_by_number[number] = candidate

    def sort_key(item: dict[str, Any]) -> tuple[int, str]:
        match = re.match(r"(\d+)([A-Z]?)", item["section_number"])
        if not match:
            return (99999, item["section_number"])
        suffix = match.group(2) or ""
        return (int(match.group(1)), suffix)

    return sorted(best_by_number.values(), key=sort_key)


def _section_entry(
    section: dict[str, Any],
    metadata: InferredLawMetadata,
    source_file: str,
) -> dict[str, Any]:
    return {
        "act_name": metadata.act_name,
        "act_id": metadata.act_id,
        "section_number": section["section_number"],
        "section_title": section["section_title"],
        "chapter": None,
        "text": section["text"],
        "jurisdiction": metadata.jurisdiction,
        "state": metadata.state,
        "domain": metadata.domain,
        "issue_tags": metadata.issue_tags,
        "effective_from": metadata.effective_from,
        "effective_to": metadata.effective_to,
        "version_date": metadata.version_date,
        "source_authority": metadata.source_authority,
        "source_url": metadata.source_url,
        "corpus_mode": "official",
        "source_file": source_file,
    }


def _generated_pack_path(source_path: Path, metadata: InferredLawMetadata) -> Path:
    return source_path.parent / f"generated_{metadata.act_id}_sections.json"


def generate_section_pack(source_path: Path, folder_domain: str) -> Path | None:
    parsed = parse_document(source_path)
    metadata = infer_law_metadata(source_path.stem, folder_domain, parsed.text)
    validation = validate_inferred_law_file(source_path, folder_domain, parsed.text, metadata)
    if validation.status == "rejected_metadata_mismatch":
        return None
    sections = extract_sections(parsed.text)
    if not sections:
        return None
    source_file = _display_path(source_path)
    payload = {
        "pack_id": f"{metadata.act_id}_sections",
        "title": f"{metadata.act_name} - section-level pack",
        "corpus_mode": "official",
        "version_date": metadata.version_date,
        "sections": [
            _section_entry(section, metadata, source_file)
            for section in sections
        ],
    }
    output_path = _generated_pack_path(source_path, metadata)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def generate_all_section_packs() -> list[Path]:
    ensure_law_pack_folders()
    outputs: list[Path] = []
    for folder in law_pack_folders():
        for source_path in sorted(folder.iterdir()):
            if not source_path.is_file() or source_path.suffix.lower() not in SUPPORTED_SOURCE_SUFFIXES:
                continue
            output = generate_section_pack(source_path, folder.name)
            if output is not None and output not in outputs:
                outputs.append(output)
    clear_law_pack_cache()
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate section-level JSON law packs from official local PDFs/TXT/DOCX.")
    parser.parse_args()
    outputs = generate_all_section_packs()
    print(f"Generated {len(outputs)} section-level law packs.")
    for path in outputs:
        print(f"- {_display_path(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
