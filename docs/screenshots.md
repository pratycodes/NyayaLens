# Screenshots

Add screenshots after running the local UI from the repo root:

```bash
python scripts/ingest_sample_corpus.py
streamlit run frontend/streamlit_app.py
```

Open:

```text
http://localhost:8501
```

## Capture Checklist

| Screenshot file | What to show | How to produce it |
| --- | --- | --- |
| `employment-analysis.png` | Full structured employment report | Select `Sample employment contract`, add `Bengaluru`, `Karnataka`, role `employee`, and query `Company is withholding salary and asking for bond recovery.` |
| `tenancy-analysis.png` | Full structured tenancy report | Select `Sample rent agreement`, add `Bengaluru`, `Karnataka`, role `tenant`, and query `Landlord deducted deposit without itemized bill.` |
| `clauses.png` | Extracted clauses section | Scroll to `Extracted Facts` and include clause cards with values and raw text. |
| `risks-and-rules.png` | Risk flags and rule checks | Scroll to `Risk Flags` and expand `Rule Checks`. |
| `citations.png` | Retrieved source excerpts and citation list | Scroll to `Retrieved Sources` and expand `Citation List`. |
| `audit-trace.png` | Explainability trail | Expand `Audit Trace`. |

## Placeholder Directory

Store final images in:

```text
docs/assets/screenshots/
```

Suggested final README embed block:

```markdown
![Employment analysis](docs/assets/screenshots/employment-analysis.png)
![Tenancy analysis](docs/assets/screenshots/tenancy-analysis.png)
![Citations](docs/assets/screenshots/citations.png)
```

Do not use screenshots that show real personal documents. Use the fake sample uploads under `data/raw/sample_uploads/`.
