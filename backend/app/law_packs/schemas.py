from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LawSection(BaseModel):
    act_name: str
    act_id: str
    section_number: str
    section_title: str
    chapter: str | None = None
    text: str
    jurisdiction: str = "India"
    state: str | None = None
    domain: str
    issue_tags: list[str] = Field(default_factory=list)
    effective_from: str
    effective_to: str | None = None
    version_date: str
    source_authority: str
    source_url: str | None = None
    corpus_mode: Literal["demo", "official", "mixed", "user_uploaded"] = "demo"
    source_file: str | None = None


class LawPack(BaseModel):
    pack_id: str
    title: str
    corpus_mode: Literal["demo", "official", "mixed", "user_uploaded"] = "demo"
    version_date: str
    sections: list[LawSection] = Field(default_factory=list)


class LawPackStatus(BaseModel):
    pack_count: int
    section_count: int
    corpus_modes: list[str]
    law_packs_loaded: list[str]
    version_dates: list[str]
