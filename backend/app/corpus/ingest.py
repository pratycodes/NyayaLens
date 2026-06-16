from __future__ import annotations

from pathlib import Path

from backend.app.config import get_settings
from backend.app.corpus.metadata import infer_document_type, infer_domain, infer_title
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


def ingest_corpus(*, include_demo: bool = True) -> list[StoredCorpusChunk]:
    if include_demo:
        ensure_sample_corpus()
    settings = get_settings()
    stored_chunks: list[StoredCorpusChunk] = []
    for path in load_corpus_files(settings.raw_laws_dir):
        parsed = parse_document(path)
        domain = infer_domain(path)
        title = infer_title(path, parsed.text)
        document_type = infer_document_type(path)
        page_chunks = chunk_pages(parsed.page_texts, prefix=path.stem, max_chars=900)
        for chunk in page_chunks:
            stored_chunks.append(
                StoredCorpusChunk(
                    chunk_id=f"{domain}-{path.stem}-{chunk.chunk_id}",
                    text=chunk.text,
                    source_file=str(path.relative_to(settings.raw_laws_dir)),
                    domain=domain,
                    jurisdiction="India",
                    document_type=document_type,
                    title=title,
                    page=chunk.page,
                )
            )
    save_corpus_chunks(stored_chunks)
    ChromaStore().upsert_chunks(stored_chunks)
    return stored_chunks
