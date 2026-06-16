# Demo Walkthrough

This walkthrough uses only synthetic sample documents and the built-in demo corpus. NyayaLens provides legal information for education and issue spotting only. It is not legal advice and does not guarantee outcomes.

## 1. Ingest The Sample Corpus

From the repo root:

```bash
cp .env.example .env
make ingest
```

This loads the demo files under `data/raw/laws/` into local SQLite and Chroma-compatible storage. Every bundled corpus file begins with:

```text
DEMO CORPUS: This is a simplified educational placeholder. Replace with official legal sources before real-world use.
```

Before real-world use, replace the demo corpus with official public legal sources and run `python scripts/ingest_corpus.py --corpus-mode official` or `--corpus-mode mixed`.

## 2. Run Backend And Frontend

Terminal 1:

```bash
make backend
```

Terminal 2:

```bash
make frontend
```

Open:

```text
http://localhost:8501
```

## 3. Analyze The Freelance Payment Demo

In the Streamlit UI:

1. Select `Demo freelance agreement`.
2. Keep dispute type as `auto-detect`.
3. Enter state `Maharashtra`, city `Mumbai`, role `freelancer`, and counterparty `Acme Demo Services LLP`.
4. Use query `I have not been paid for the last invoice.`
5. Click `Analyze`.

You should see:

- Overview tab: `Unpaid compensation / pending payment`, `Contract payment`, `Freelance/service agreement`.
- Key facts table: company/client, freelancer role, invoice timing, payment timing, compensation, TDS, arbitration, and jurisdiction.
- Risks & Remedies tab: unpaid compensation risk, missing payment evidence, contractor/freelancer route ambiguity, payment/invoice clause comparison, TDS clarification, and arbitration/jurisdiction path.
- Document Review tab: cited sections with page-level evidence and highlights when a PDF is uploaded.
- Sources & Citations tab: uploaded-document citations separated from demo corpus citations.
- Drafts & Checklist tab: company/client/accounts wording, not HR/payroll wording.
- Evaluation / Trust tab: demo corpus mode, hash retrieval mode, missing facts, human review reasons, and citation coverage.

## 4. Analyze The Employment Exit Demo

Select `Demo employment exit agreement` and use:

- State: `Karnataka`
- City: `Bengaluru`
- Role: `employee`
- Query: `Company is withholding salary and asking for bond recovery.`

Expected report:

- employment issue/domain
- notice period, training bond, non-compete, FNF, confidentiality, arbitration, and jurisdiction facts
- high/medium risk flags for bond, non-compete, long notice, settlement withholding, and dispute path
- HR/payroll-oriented draft only because the context is employment

## 5. Analyze The Tenant Deposit Demo

Select `Demo rent agreement` and use:

- State: `Karnataka`
- City: `Bengaluru`
- Role: `tenant`
- Counterparty: `Demo Landlord`
- Query: `Landlord deducted deposit without itemized bill.`

Expected report:

- tenancy issue/domain
- rent, security deposit, lock-in, notice, repairs, eviction, and jurisdiction facts
- deposit-deduction and repair-evidence risks
- landlord/deposit-focused next steps and evidence checklist

## 6. Optional PDF Demo

Generate synthetic PDFs:

```bash
make demo-pdfs
```

Upload `data/raw/sample_uploads/demo_freelance_agreement.pdf` to exercise the Document Review tab. The viewer renders PDF pages locally with PyMuPDF and highlights matching quotes when possible.

## 7. Generate Demo Outputs

```bash
make demo-reports
```

Outputs:

```text
demo_outputs/freelance_payment_report.json
demo_outputs/employment_exit_report.json
demo_outputs/tenant_deposit_report.json
demo_outputs/unsafe_request_report.json
demo_outputs/eval_summary.json
demo_outputs/eval_summary.md
```

These files use only fake sample data and are safe to commit.
