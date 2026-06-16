from __future__ import annotations

import re

from backend.app.storage.models import StoredCorpusChunk

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_+-]*")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class BM25Store:
    def __init__(self, chunks: list[StoredCorpusChunk]) -> None:
        self.chunks = chunks
        self.tokens = [tokenize(chunk.text) for chunk in chunks]
        self._bm25 = None
        try:
            from rank_bm25 import BM25Okapi  # type: ignore

            self._bm25 = BM25Okapi(self.tokens)
        except Exception:
            self._bm25 = None

    def query(self, query: str, *, k: int = 5, domain: str | None = None) -> list[tuple[StoredCorpusChunk, float]]:
        allowed = [
            (idx, chunk)
            for idx, chunk in enumerate(self.chunks)
            if not domain or domain == "unknown" or chunk.domain == domain
        ]
        if not allowed:
            return []
        query_tokens = tokenize(query)
        if self._bm25 is not None:
            scores = self._bm25.get_scores(query_tokens)
            ranked = [(chunk, float(scores[idx])) for idx, chunk in allowed]
        else:
            query_set = set(query_tokens)
            ranked = [
                (chunk, float(len(query_set.intersection(set(self.tokens[idx])))))
                for idx, chunk in allowed
            ]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:k]
