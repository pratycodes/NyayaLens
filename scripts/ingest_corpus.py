# ruff: noqa: E402
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.corpus.ingest import ingest_corpus


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest NyayaLens demo, official, or mixed corpus files.")
    parser.add_argument(
        "--corpus-mode",
        choices=["demo", "official", "mixed"],
        default="demo",
        help="Corpus set to ingest. Official mode reads local files under data/raw/official/.",
    )
    args = parser.parse_args()
    chunks = ingest_corpus(
        include_demo=args.corpus_mode in {"demo", "mixed"},
        corpus_mode=args.corpus_mode,
    )
    print(f"Ingested {len(chunks)} chunks in {args.corpus_mode} mode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
