#!/usr/bin/env bash
set -euo pipefail

rm -f data/sqlite/nyayalens.db data/sqlite/nyayalens.db-*
rm -f data/vectorstore/chroma/fallback_store.json
find data/processed -type f ! -name .gitkeep -delete
python scripts/ingest_sample_corpus.py
