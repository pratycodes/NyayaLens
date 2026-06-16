# Deployment QA Checklist

Use this checklist for Streamlit Cloud or another hosted NyayaLens demo. Do not run heavy load tests against the public deployed app. Use `tests/load/locustfile.py` against a local FastAPI backend instead.

## Access And Cold Start

- Open the deployed URL in an incognito/private window.
- Confirm the app loads from a cold start without Python import errors.
- Confirm no API keys or secrets are shown in Streamlit logs or UI.
- Refresh the app once after cold start and confirm state resets safely.
- Confirm the legal-information disclaimer is visible in the report flow.

## Viewports

- Desktop: verify Overview, Risks & Remedies, Document Review, Sources & Citations, Law Cross-Reference, Drafts & Checklist, Evaluation / Trust, and Audit / Debug tabs.
- Mobile viewport: verify sidebar controls remain usable and tables do not block analysis.
- Confirm no raw enum names appear in the main UI.
- Confirm raw clauses and debug JSON are only visible in Audit / Debug.

## Upload And Analysis

- Upload synthetic freelance PDF and run unpaid-payment analysis.
- Upload synthetic rent agreement and run deposit-deduction analysis.
- Upload synthetic employment agreement and run notice/bond/FNF analysis.
- Repeat the same upload twice in one session.
- Open a second browser/incognito session and confirm reports do not leak between sessions.
- Try a corrupt PDF and confirm the app shows a graceful error.
- Try an empty/scanned-like PDF and confirm OCR/no-text warnings are clear.
- Try a file over the configured local-demo limit and confirm rejection is graceful.

## Evidence And Export

- Confirm key facts show concise citation chips.
- Confirm Document Review can show cited PDF pages.
- Confirm missing exact highlight falls back to page-level quote display.
- Confirm Sources & Citations separates uploaded-document citations from legal/demo corpus citations.
- Download Markdown and JSON report exports.
- Confirm exports do not include secrets, absolute local paths, or private documents from another session.

## Law-Pack And Trust Panel

- Confirm law-pack coverage table is visible in Evaluation / Trust.
- Confirm demo/official/missing/historical statuses are readable.
- Confirm Bihar private tenancy coverage is shown as missing if still unresolved.
- Confirm UP tenancy OCR-derived text warning is visible.
- Confirm current criminal-law screening prefers BNS/BNSS/BSA after 2024-07-01.
- Confirm IPC/CrPC/Evidence Act are described as historical for pre-2024-07-01 disputes.

## Concurrency And Caching

- Run two concurrent browser sessions with different synthetic documents.
- Confirm each session sees only its own report.
- Confirm cached corpus/law-pack loading does not mix uploaded document text across sessions.
- Confirm repeated analysis does not create stale citation chips from a prior report.

## Local-Only Load Check

Run local backend first:

```bash
sh scripts/run_backend.sh
```

Then run local load test:

```bash
make load-local
```

Do not point Locust at the public Streamlit Cloud URL.
