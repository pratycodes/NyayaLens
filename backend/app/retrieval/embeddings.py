from __future__ import annotations

import hashlib
import logging
import math
import re
from functools import lru_cache

from backend.app.config import get_settings

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_+-]*")
LOGGER = logging.getLogger(__name__)


class EmbeddingModel:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class HashingEmbeddingModel(EmbeddingModel):
    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in TOKEN_RE.findall(text.lower()):
                digest = hashlib.md5(token.encode("utf-8")).hexdigest()
                index = int(digest[:8], 16) % self.dimensions
                sign = 1.0 if int(digest[8:10], 16) % 2 == 0 else -1.0
                vector[index] += sign
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


class SentenceTransformerEmbeddingModel(EmbeddingModel):
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model = SentenceTransformer(model_name, local_files_only=True)

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return [list(map(float, row)) for row in embeddings]


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    settings = get_settings()
    if settings.embedding_backend.lower() not in {"sentence-transformers", "sbert"}:
        return HashingEmbeddingModel()
    try:
        return SentenceTransformerEmbeddingModel(settings.embedding_model)
    except Exception as exc:
        LOGGER.warning(
            "Sentence-transformers backend unavailable; falling back to lightweight hashing: %s",
            exc,
        )
        return HashingEmbeddingModel()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=False))
