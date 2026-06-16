from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from backend.app.law_packs.registry import official_law_pack_root


class LawPackManifestEntry(BaseModel):
    act_id: str
    expected_title: str
    expected_act_no: str | None = None
    domain: str
    jurisdiction: str
    historical: bool
    effective_from: str | None = None
    effective_to: str | None = None
    required_for_official_mode: bool
    allowed_aliases: list[str] = Field(default_factory=list)
    expected_source_files: list[str] = Field(default_factory=list)
    source_authority: str
    notes: str = ""


class LawPackManifest(BaseModel):
    version: str = "1.0"
    entries: list[LawPackManifestEntry] = Field(default_factory=list)


def manifest_path(root: Path | None = None) -> Path:
    return (root or official_law_pack_root()) / "law_pack_manifest.json"


@lru_cache(maxsize=4)
def _load_manifest_cached(path: str) -> LawPackManifest:
    manifest_file = Path(path)
    if not manifest_file.exists():
        return LawPackManifest()
    return LawPackManifest(**json.loads(manifest_file.read_text(encoding="utf-8")))


def load_law_pack_manifest(root: Path | None = None) -> LawPackManifest:
    return _load_manifest_cached(str(manifest_path(root).resolve()))


def manifest_entries_by_act_id(root: Path | None = None) -> dict[str, LawPackManifestEntry]:
    return {entry.act_id: entry for entry in load_law_pack_manifest(root).entries}
