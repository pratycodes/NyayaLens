from __future__ import annotations

from pathlib import Path

from backend.app.config import get_settings

LAW_PACK_DOMAINS = [
    "contract",
    "labour",
    "criminal",
    "constitution",
    "tenancy",
    "legal_aid",
]


def official_law_pack_root() -> Path:
    return get_settings().raw_laws_dir.parent / "official"


def law_pack_folders(root: Path | None = None) -> list[Path]:
    base = root or official_law_pack_root()
    return [base / domain for domain in LAW_PACK_DOMAINS]


def ensure_law_pack_folders(root: Path | None = None) -> None:
    base = root or official_law_pack_root()
    for folder in law_pack_folders(root):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / ".gitkeep").touch(exist_ok=True)
    quarantine = base / "_quarantine"
    quarantine.mkdir(parents=True, exist_ok=True)
    (quarantine / ".gitkeep").touch(exist_ok=True)
