from __future__ import annotations

from fastapi import APIRouter

from backend.app.config import get_settings
from backend.app.core.schemas import CorpusStatus
from backend.app.corpus.ingest import ingest_corpus
from backend.app.storage.sqlite import corpus_status

router = APIRouter(prefix="/corpus", tags=["corpus"])


@router.post("/ingest")
def ingest() -> dict[str, int | str]:
    chunks = ingest_corpus(include_demo=True)
    return {"status": "ok", "chunks": len(chunks)}


@router.get("/status", response_model=CorpusStatus)
def status() -> CorpusStatus:
    settings = get_settings()
    count, files = corpus_status()
    using_demo = any(file.endswith("_general_information.txt") for file in files)
    return CorpusStatus(
        chunk_count=count,
        source_files=files,
        using_demo_corpus=using_demo,
        persist_dir=str(settings.chroma_persist_dir),
    )
