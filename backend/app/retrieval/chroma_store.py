from __future__ import annotations

import json
import logging
from contextlib import suppress

from backend.app.config import get_settings
from backend.app.retrieval.embeddings import cosine_similarity, get_embedding_model
from backend.app.storage.models import StoredCorpusChunk

LOGGER = logging.getLogger(__name__)


class ChromaStore:
    """Chroma-compatible local store with a JSON fallback for offline test runs."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.fallback_path = self.settings.chroma_persist_dir / "fallback_store.json"
        self._client = None
        self._collection = None
        if self.settings.embedding_backend.lower() == "hash":
            return
        try:
            import chromadb  # type: ignore

            self._client = chromadb.PersistentClient(path=str(self.settings.chroma_persist_dir))
            self._collection = self._client.get_or_create_collection(
                "nyayalens_law_chunks",
                embedding_function=None,
            )
        except Exception as exc:
            LOGGER.warning("ChromaDB unavailable; using JSON vector fallback: %s", exc)
            self._client = None
            self._collection = None

    def reset(self) -> None:
        if self.fallback_path.exists():
            self.fallback_path.unlink()
        if self._client is None:
            return
        with suppress(Exception):
            self._client.delete_collection("nyayalens_law_chunks")
        self._collection = self._client.get_or_create_collection(
            "nyayalens_law_chunks",
            embedding_function=None,
        )

    def upsert_chunks(self, chunks: list[StoredCorpusChunk]) -> None:
        if not chunks:
            return
        embeddings = get_embedding_model().embed([chunk.text for chunk in chunks])
        metadatas = [
            {
                "source_file": chunk.source_file,
                "domain": chunk.domain,
                "jurisdiction": chunk.jurisdiction,
                "document_type": chunk.document_type,
                "title": chunk.title,
                "page": chunk.page,
                "chunk_id": chunk.chunk_id,
                "corpus_mode": chunk.corpus_mode,
                "source_authority": chunk.source_authority,
                "source_url": chunk.source_url,
                "state": chunk.state,
                "effective_date": chunk.effective_date,
                "version_date": chunk.version_date,
            }
            for chunk in chunks
        ]
        if self._collection is not None:
            self._collection.upsert(
                ids=[chunk.chunk_id for chunk in chunks],
                documents=[chunk.text for chunk in chunks],
                metadatas=metadatas,
                embeddings=embeddings,
            )
            return
        self.fallback_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": metadata,
                "embedding": embedding,
            }
            for chunk, metadata, embedding in zip(chunks, metadatas, embeddings, strict=True)
        ]
        self.fallback_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def query(self, query: str, *, k: int = 5, domain: str | None = None) -> list[dict]:
        if self._collection is not None:
            where = {"domain": domain} if domain and domain != "unknown" else None
            try:
                result = self._collection.query(
                    query_embeddings=get_embedding_model().embed([query]),
                    n_results=k,
                    where=where,
                    include=["documents", "metadatas", "distances"],
                )
                rows: list[dict] = []
                for idx, doc_id in enumerate(result.get("ids", [[]])[0]):
                    metadata = result.get("metadatas", [[]])[0][idx] or {}
                    rows.append(
                        {
                            "id": doc_id,
                            "text": result.get("documents", [[]])[0][idx],
                            "metadata": metadata,
                            "score": 1.0 - float(result.get("distances", [[]])[0][idx]),
                        }
                    )
                return rows
            except Exception as exc:
                LOGGER.warning("Chroma query failed; using JSON vector fallback: %s", exc)

        if not self.fallback_path.exists():
            return []
        payload = json.loads(self.fallback_path.read_text(encoding="utf-8"))
        query_embedding = get_embedding_model().embed([query])[0]
        rows = []
        for item in payload:
            metadata = item["metadata"]
            if domain and domain != "unknown" and metadata.get("domain") != domain:
                continue
            rows.append(
                {
                    "id": item["id"],
                    "text": item["text"],
                    "metadata": metadata,
                    "score": cosine_similarity(query_embedding, item["embedding"]),
                }
            )
        rows.sort(key=lambda row: row["score"], reverse=True)
        return rows[:k]
