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
