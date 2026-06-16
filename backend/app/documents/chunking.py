from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    chunk_id: str
    text: str
    page: int | None = None


def chunk_text(text: str, *, prefix: str, page: int | None = None, max_chars: int = 900) -> list[TextChunk]:
    normalized = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not normalized:
        return []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
    chunks: list[TextChunk] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        if current and current_len + len(paragraph) > max_chars:
            chunk_text_value = "\n\n".join(current)
            chunks.append(TextChunk(chunk_id=f"{prefix}-{len(chunks)+1}", text=chunk_text_value, page=page))
            current = []
            current_len = 0
        current.append(paragraph)
        current_len += len(paragraph)
    if current:
        chunks.append(TextChunk(chunk_id=f"{prefix}-{len(chunks)+1}", text="\n\n".join(current), page=page))
    return chunks


def chunk_pages(page_texts: list[tuple[int, str]], *, prefix: str, max_chars: int = 900) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for page, text in page_texts:
        page_chunks = chunk_text(text, prefix=f"{prefix}-p{page}", page=page, max_chars=max_chars)
        chunks.extend(page_chunks)
    return chunks
