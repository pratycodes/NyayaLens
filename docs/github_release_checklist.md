# GitHub Release Checklist

Use this checklist before making the repository public or tagging a portfolio release.

## Repository Metadata

- Set GitHub About description:
  - `Evidence-grounded legal issue triage and document review for Indian employment, freelance-payment, and tenancy disputes.`
- Set website to the deployed Streamlit URL:
  - `https://nyayalens.streamlit.app`
- Add topics:
  - `legal-ai`
  - `rag`
  - `streamlit`
  - `fastapi`
  - `langgraph`
  - `document-ai`
  - `explainable-ai`
  - `india`
  - `law`
  - `legal-tech`

## Public Demo

- Verify the Streamlit app opens in an incognito/private browser window.
- Verify mobile layout at a narrow viewport.
- Verify screenshots under `docs/assets/screenshots/` use synthetic demo documents only.
- Verify README links to the live demo and screenshot assets.
- Verify public demo reports under `demo_outputs/` use fake names only.

## Release Quality

- Run `python -m ruff check .`.
- Run `python -m pytest`.
- Run `python scripts/ingest_law_packs.py`.
- Run `python scripts/ingest_corpus.py --corpus-mode mixed`.
- Run `python scripts/generate_demo_reports.py`.
- Run `python scripts/run_eval.py`.
- Run `python scripts/run_eval.py --scenario-file eval/stress_scenarios.json --output demo_outputs/stress_eval_summary.json`.
- Review `demo_outputs/law_pack_coverage.json` for missing or rejected packs.
- Review `demo_outputs/stress_eval_summary.md` for false unsafe refusals, false tenancy routes, raw enum leakage, and hallucinated section count.

## Privacy And Safety

- Confirm no private contracts, resumes, signatures, addresses, or real client/company names are committed.
- Confirm official PDFs and generated law-pack JSONs are documented as reproducibility assets.
- Confirm the app says legal information only, not legal advice.
- Confirm unsafe requests are refused and victim/reporting contexts are not falsely refused.

## Versioning

- Create release tag `v0.1.0` after the checks above pass.
- Attach a short release note with:
  - core product flow
  - supported domains
  - mock/offline mode
  - law-pack coverage caveats
  - stress-eval summary
