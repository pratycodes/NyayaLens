from __future__ import annotations

from pathlib import Path


def infer_domain(path: Path) -> str:
    parts = {part.lower() for part in path.parts}
    if "employment" in parts:
        return "employment"
    if "labour" in parts:
        return "employment"
    if "tenancy" in parts:
        return "tenancy"
    if "consumer" in parts:
        return "consumer"
    if "legal_aid" in parts:
        return "legal_aid"
    if "grievance" in parts:
        return "grievance"
    return "general"


def infer_corpus_mode(path: Path) -> str:
    parts = {part.lower() for part in path.parts}
    if "official" in parts:
        return "official"
    if "laws" in parts:
        return "demo"
    return "user_uploaded"


def infer_source_authority(path: Path) -> str | None:
    parts = {part.lower() for part in path.parts}
    if "india_code" in parts:
        return "India Code"
    if "labour" in parts:
        return "Labour department / public source"
    if "tenancy" in parts:
        return "State tenancy / rent authority source"
    if "legal_aid" in parts:
        return "Legal aid public source"
    return None


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
