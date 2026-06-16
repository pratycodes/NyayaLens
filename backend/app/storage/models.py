from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StoredCorpusChunk:
    chunk_id: str
    text: str
    source_file: str
    domain: str
    jurisdiction: str
    document_type: str
    title: str
    page: int | None = None
    corpus_mode: str = "demo"
    source_authority: str | None = None
    source_url: str | None = None
    state: str | None = None
    effective_date: str | None = None
    version_date: str | None = None
