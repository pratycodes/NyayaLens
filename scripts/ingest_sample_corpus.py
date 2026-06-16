# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.corpus.ingest import ingest_corpus

if __name__ == "__main__":
    chunks = ingest_corpus(include_demo=True, corpus_mode="demo")
    print(f"Ingested {len(chunks)} corpus chunks.")
