# Screenshots

Use only synthetic demo documents for public screenshots. Do not capture real uploaded documents or personal/company details.

Run from the repo root:

```bash
python scripts/ingest_sample_corpus.py
streamlit run frontend/streamlit_app.py
```

Open:

```text
http://localhost:8501
```

## Capture Checklist

| Screenshot file | Tab | What to show |
| --- | --- | --- |
| `overview.png` | Overview | Summary cards and concise key facts table for `Demo freelance agreement`. |
| `risk-table.png` | Risks & Remedies | Filterable risk table and possible counterparty arguments. |
| `document-review.png` | Document Review | PDF or text evidence viewer with important sections and selected citation. |
| `sources-citations.png` | Sources & Citations | Uploaded-document citations separated from legal/demo corpus citations. |
| `draft-checklist.png` | Drafts & Checklist | Safe next steps, evidence checklist, and company/client/accounts draft. |
| `trust-panel.png` | Evaluation / Trust | Corpus mode, retrieval mode, human review reasons, and citation coverage. |
| `audit-debug.png` | Audit / Debug | Raw enums, extracted clauses, retrieval scores, rule checks, verifier, and audit trace. |

## Suggested Demo Inputs

Freelance payment:

- Sample: `Demo freelance agreement`
- Role: `freelancer`
- State/city: `Maharashtra`, `Mumbai`
- Query: `I have not been paid for the last invoice.`

Tenant deposit:

- Sample: `Demo rent agreement`
- Role: `tenant`
- State/city: `Karnataka`, `Bengaluru`
- Query: `Landlord deducted deposit without itemized bill.`

## Placeholder Directory

Store final images in:

```text
docs/assets/screenshots/
```

The directory is tracked by `docs/assets/screenshots/.gitkeep`.
