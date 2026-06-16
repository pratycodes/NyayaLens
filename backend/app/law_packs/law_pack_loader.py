from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.app.config import ROOT_DIR
from backend.app.documents.parsers import parse_document
from backend.app.law_packs.official_source_metadata import infer_law_metadata
from backend.app.law_packs.registry import ensure_law_pack_folders, law_pack_folders
from backend.app.law_packs.schemas import LawPack, LawPackStatus, LawSection
from backend.app.law_packs.validation import validate_inferred_law_file

SUPPORTED_LAW_PACK_SUFFIXES = {".json", ".txt", ".pdf", ".docx"}


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT_DIR))
    except ValueError:
        return path.name


def _load_json_pack(path: Path) -> LawPack:
    data = json.loads(path.read_text(encoding="utf-8"))
    pack = LawPack(**data)
    for section in pack.sections:
        section.source_file = section.source_file or _display_path(path)
        if section.corpus_mode == "mixed":
            section.corpus_mode = pack.corpus_mode
    return pack


def _load_document_section(path: Path, domain: str, root: Path | None = None) -> LawPack | None:
    parsed = parse_document(path)
    corpus_mode = "official" if "official" in path.parts and "demo" not in path.name.lower() else "demo"
    metadata = infer_law_metadata(path.stem, domain, parsed.text)
    validation = validate_inferred_law_file(path, domain, parsed.text, metadata, root=root)
    if validation.status == "rejected_metadata_mismatch":
        return None
    section = LawSection(
        act_name=metadata.act_name,
        act_id=metadata.act_id,
        section_number=metadata.section_number,
        section_title=metadata.section_title,
        text=parsed.text[:4000],
        jurisdiction=metadata.jurisdiction,
        state=metadata.state,
        domain=metadata.domain,
        issue_tags=metadata.issue_tags,
        effective_from=metadata.effective_from,
        effective_to=metadata.effective_to,
        version_date=metadata.version_date,
        source_authority=metadata.source_authority,
        source_url=metadata.source_url,
        corpus_mode=corpus_mode,  # type: ignore[arg-type]
        source_file=_display_path(path),
    )
    return LawPack(
        pack_id=metadata.act_id,
        title=metadata.act_name,
        corpus_mode=corpus_mode,  # type: ignore[arg-type]
        version_date=metadata.version_date,
        sections=[section],
    )


def _root_cache_key(root: Path | None) -> str:
    return str(root.resolve()) if root else ""


@lru_cache(maxsize=4)
def _load_law_packs_cached(root_key: str) -> tuple[LawPack, ...]:
    root = Path(root_key) if root_key else None
    ensure_law_pack_folders(root)
    packs: list[LawPack] = []
    for folder in law_pack_folders(root):
        domain = folder.name
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_LAW_PACK_SUFFIXES:
                continue
            if path.name == ".gitkeep":
                continue
            if path.suffix.lower() == ".json":
                packs.append(_load_json_pack(path))
            else:
                pack = _load_document_section(path, domain, root=root)
                if pack is not None:
                    packs.append(pack)
    return tuple(packs)


def load_law_packs(root: Path | None = None) -> list[LawPack]:
    return [pack.model_copy(deep=True) for pack in _load_law_packs_cached(_root_cache_key(root))]


def clear_law_pack_cache() -> None:
    _load_law_packs_cached.cache_clear()


def load_law_sections(root: Path | None = None) -> list[LawSection]:
    sections: list[LawSection] = []
    for pack in load_law_packs(root):
        sections.extend(pack.sections)
    return sections


def law_pack_status(root: Path | None = None) -> LawPackStatus:
    packs = load_law_packs(root)
    sections = [section for pack in packs for section in pack.sections]
    return LawPackStatus(
        pack_count=len(packs),
        section_count=len(sections),
        corpus_modes=sorted({section.corpus_mode for section in sections}),
        law_packs_loaded=sorted({pack.title for pack in packs}),
        version_dates=sorted({section.version_date for section in sections if section.version_date}),
    )
