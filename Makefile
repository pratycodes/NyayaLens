.PHONY: install test lint ingest backend frontend reset

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest

lint:
	python -m ruff check .

ingest:
	python scripts/ingest_sample_corpus.py

backend:
	sh scripts/run_backend.sh

frontend:
	streamlit run frontend/streamlit_app.py

reset:
	sh scripts/reset_local_data.sh
