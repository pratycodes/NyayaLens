from __future__ import annotations

from backend.app.core.schemas import Citation, RetrievedSource
from backend.app.corpus.ingest import ingest_corpus
from backend.app.retrieval.bm25_store import BM25Store
from backend.app.retrieval.chroma_store import ChromaStore
from backend.app.retrieval.reranker import rerank_sources
from backend.app.storage.models import StoredCorpusChunk
from backend.app.storage.sqlite import load_corpus_chunks


def _to_source(chunk: StoredCorpusChunk, score: float) -> RetrievedSource:
    excerpt = chunk.text.strip()
    if len(excerpt) > 600:
        excerpt = excerpt[:597].rstrip() + "..."
    return RetrievedSource(
        citation=Citation(
            source_file=chunk.source_file,
            title=chunk.title,
            domain=chunk.domain,
            jurisdiction=chunk.jurisdiction,
            page=chunk.page,
            chunk_id=chunk.chunk_id,
            excerpt=excerpt,
        ),
        score=score,
    )


class HybridRetriever:
    def __init__(self) -> None:
        self.chroma = ChromaStore()

    def _chunks(self) -> list[StoredCorpusChunk]:
        chunks = load_corpus_chunks()
        if chunks:
            return chunks
        return ingest_corpus(include_demo=True)

    def retrieve(self, query: str, *, domain: str | None = None, k: int = 5) -> list[RetrievedSource]:
        chunks = self._chunks()
        by_id = {chunk.chunk_id: chunk for chunk in chunks}
        bm25_rows = BM25Store(chunks).query(query, domain=domain, k=k * 2)
        sources = [_to_source(chunk, score / 10.0) for chunk, score in bm25_rows]

        for row in self.chroma.query(query, domain=domain, k=k * 2):
            chunk_id = row["metadata"].get("chunk_id") or row["id"]
            chunk = by_id.get(chunk_id)
            if chunk:
                sources.append(_to_source(chunk, float(row["score"])))

        if not sources and chunks:
            fallback = [chunk for chunk in chunks if not domain or domain == "unknown" or chunk.domain == domain]
            sources.extend(_to_source(chunk, 0.01) for chunk in fallback[:k])
        return rerank_sources(sources, k=k)
