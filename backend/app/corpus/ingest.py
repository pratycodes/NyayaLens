from __future__ import annotations

from pathlib import Path

from backend.app.config import get_settings
from backend.app.corpus.metadata import (
    infer_corpus_mode,
    infer_document_type,
    infer_domain,
    infer_source_authority,
    infer_title,
)
from backend.app.corpus.sample_corpus import ensure_sample_corpus
from backend.app.documents.chunking import chunk_pages
from backend.app.documents.parsers import parse_document
from backend.app.retrieval.chroma_store import ChromaStore
from backend.app.storage.models import StoredCorpusChunk
from backend.app.storage.sqlite import save_corpus_chunks

SUPPORTED_SUFFIXES = {".txt", ".pdf", ".docx"}


def load_corpus_files(root: Path | None = None) -> list[Path]:
    settings = get_settings()
    root = root or settings.raw_laws_dir
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    return sorted(files)


def _roots_for_mode(mode: str) -> list[Path]:
    settings = get_settings()
    official_root = settings.raw_laws_dir.parent / "official"
    if mode == "demo":
        return [settings.raw_laws_dir]
    if mode == "official":
        return [official_root]
    if mode == "mixed":
        return [settings.raw_laws_dir, official_root]
    return [settings.raw_laws_dir]


def ingest_corpus(*, include_demo: bool = True, corpus_mode: str = "demo") -> list[StoredCorpusChunk]:
    if include_demo and corpus_mode in {"demo", "mixed"}:
        ensure_sample_corpus()
    stored_chunks: list[StoredCorpusChunk] = []
    for root in _roots_for_mode(corpus_mode):
        if not root.exists():
            continue
        files = load_corpus_files(root)
        for path in files:
            parsed = parse_document(path)
            domain = infer_domain(path)
            title = infer_title(path, parsed.text)
            document_type = infer_document_type(path)
            mode = infer_corpus_mode(path)
            page_chunks = chunk_pages(parsed.page_texts, prefix=path.stem, max_chars=900)
            for chunk in page_chunks:
                stored_chunks.append(
                    StoredCorpusChunk(
                        chunk_id=f"{mode}-{domain}-{path.stem}-{chunk.chunk_id}",
                        text=chunk.text,
                        source_file=str(path.relative_to(root)),
                        domain=domain,
                        jurisdiction="India",
                        document_type=document_type,
                        title=title,
                        page=chunk.page,
                        corpus_mode=mode,
                        source_authority=infer_source_authority(path),
                    )
                )
    save_corpus_chunks(stored_chunks)
    vector_store = ChromaStore()
    vector_store.reset()
    vector_store.upsert_chunks(stored_chunks)
    return stored_chunks
