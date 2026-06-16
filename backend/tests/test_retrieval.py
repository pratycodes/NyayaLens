from __future__ import annotations

from backend.app.corpus.ingest import ingest_corpus
from backend.app.retrieval.hybrid_retriever import HybridRetriever


def test_retrieval_returns_citations() -> None:
    ingest_corpus(include_demo=True)
    sources = HybridRetriever().retrieve("employment bond training recovery", domain="employment", k=3)
    assert sources
    assert sources[0].citation.source_file
    assert sources[0].citation.excerpt
