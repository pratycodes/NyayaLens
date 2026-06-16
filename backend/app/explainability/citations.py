from __future__ import annotations

from backend.app.core.schemas import Citation, RetrievedSource


def collect_citations(sources: list[RetrievedSource]) -> list[Citation]:
    seen: set[tuple[str, str | None]] = set()
    citations: list[Citation] = []
    for source in sources:
        key = (source.citation.source_file, source.citation.chunk_id)
        if key in seen:
            continue
        seen.add(key)
        citations.append(source.citation)
    return citations
