from __future__ import annotations

from pathlib import Path


def infer_domain(path: Path) -> str:
    parts = {part.lower() for part in path.parts}
    if "employment" in parts:
        return "employment"
    if "tenancy" in parts:
        return "tenancy"
    return "general"


def infer_document_type(path: Path) -> str:
    name = path.name.lower()
    if "contract" in name:
        return "contract_general_information"
    if "legal_aid" in name:
        return "legal_aid_general_information"
    if "tenancy" in name:
        return "tenancy_general_information"
    if "employment" in name:
        return "employment_general_information"
    return "general_information"


def infer_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("DEMO CORPUS"):
            return stripped[:120]
    return path.stem.replace("_", " ").title()
