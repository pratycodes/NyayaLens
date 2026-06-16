from __future__ import annotations

from backend.app.core.schemas import RetrievedSource


def rerank_sources(sources: list[RetrievedSource], *, k: int = 5) -> list[RetrievedSource]:
    seen: set[str] = set()
    deduped: list[RetrievedSource] = []
    for source in sorted(sources, key=lambda item: item.score, reverse=True):
        key = source.citation.chunk_id or source.citation.excerpt[:80]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(source)
    return deduped[:k]
