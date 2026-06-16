.PHONY: install install-optional ingest law-packs section-law-packs backend frontend test lint demo-reports demo-pdfs clean-local reset

install:
	python -m pip install -r requirements.txt

install-optional:
	python -m pip install -r requirements-optional.txt

ingest:
	python scripts/ingest_sample_corpus.py

law-packs:
	python scripts/ingest_law_packs.py

section-law-packs:
	python scripts/generate_section_law_packs.py

backend:
	sh scripts/run_backend.sh

frontend:
	streamlit run frontend/streamlit_app.py

test:
	python -m pytest

lint:
	python -m ruff check .

demo-reports:
	python scripts/generate_demo_reports.py
	python scripts/run_eval.py

demo-pdfs:
	python scripts/generate_demo_pdfs.py

clean-local:
	sh scripts/reset_local_data.sh

reset:
	sh scripts/reset_local_data.sh
