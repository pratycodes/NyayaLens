.PHONY: install install-dev install-optional ingest law-packs section-law-packs backend frontend test lint demo-reports demo-pdfs stress-docs stress-eval public-smoke ui-test e2e-local load-local all-checks clean-local reset

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements.txt
	python -m pip install -r requirements-dev.txt

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

stress-docs:
	python scripts/generate_stress_docs.py

stress-eval: stress-docs
	python scripts/run_eval.py --scenario-file eval/stress_scenarios.json --output demo_outputs/stress_eval_summary.json

public-smoke:
	python scripts/run_eval.py
	python scripts/run_eval.py --scenario-file eval/stress_scenarios.json --output demo_outputs/stress_eval_summary.json
	@echo "For deployed UI smoke, set NYAYALENS_APP_URL and run: python -m pytest tests/e2e -q"

ui-test:
	python -m pytest tests/ui -q

e2e-local: stress-docs
	NYAYALENS_APP_URL=$${NYAYALENS_APP_URL:-http://localhost:8501} python -m pytest tests/e2e -q

load-local: stress-docs
	python -m locust -f tests/load/locustfile.py --host http://127.0.0.1:8000

all-checks: law-packs
	python scripts/ingest_corpus.py --corpus-mode mixed
	python scripts/run_eval.py
	python scripts/run_eval.py --scenario-file eval/stress_scenarios.json --output demo_outputs/stress_eval_summary.json
	python -m pytest
	python -m ruff check .

clean-local:
	sh scripts/reset_local_data.sh

reset:
	sh scripts/reset_local_data.sh
