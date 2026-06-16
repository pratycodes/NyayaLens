from __future__ import annotations

from pathlib import Path

from backend.app.law_packs.law_pack_loader import load_law_sections
from backend.app.law_packs.registry import ensure_law_pack_folders
from backend.app.law_packs.schemas import LawSection


def ingest_law_packs(root: Path | None = None) -> list[LawSection]:
    ensure_law_pack_folders(root)
    return load_law_sections(root)
