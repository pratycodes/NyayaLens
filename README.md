# NyayaLens

Explainable Legal-Rights Agent for Indian Employment Exit and Tenancy Disputes.

NyayaLens is an end-to-end AI engineering resume project built for a 4th-year B.Tech Mathematics and Computing student in India. It is not a generic "chat with laws" app. The product flow is structured:

```text
upload document
  -> parse text
  -> extract clauses
  -> detect issue
  -> infer missing context
  -> route expert
  -> retrieve local sources
  -> run deterministic rules
  -> verify safety and citations
  -> explain risk
  -> suggest safe next steps
```

NyayaLens provides legal information for education and issue spotting only. It is not legal advice and does not create a lawyer-client relationship.

## Social Impact

Employment exits and rental disputes are common, stressful, and document-heavy. NyayaLens helps users organize facts, identify risky clauses, preserve evidence, and ask safer written questions before escalation. The app avoids outcome guarantees and points users toward qualified legal aid for high-risk decisions.

## Why This Is More Than RAG

NyayaLens combines retrieval with deterministic checks and verification:

- Clause extraction finds notice periods, bonds, non-competes, deposits, eviction clauses, jurisdiction, arbitration, and settlement language.
- MoE-style routing selects domain experts such as `EmploymentExitExpert`, `TenancyExpert`, `ContractClauseExpert`, and `LegalAidSafetyExpert`.
- RAG retrieves from a local corpus and shows citations.
- Rules convert extracted facts into risk flags with evidence and next steps.
- A verifier blocks overclaimed jurisdiction, uncited exact section claims, unsafe requests, and guaranteed outcomes.

## Architecture

```text
Streamlit UI
    |
FastAPI API
    |
LangGraph-compatible workflow
    |
    +-- document parsers: TXT, PDF, DOCX, optional OCR hook
    +-- clause extractor: regex and heuristics
    +-- issue spotter: mock keyword mode, optional LLM JSON mode
    +-- expert router: MoE-style domain routing
    +-- retrieval: BM25 + Chroma-compatible vector store
    +-- rules: employment and tenancy risk checks
    +-- verifier: citation, safety, jurisdiction, disclaimer checks
    +-- remedy planner: safe next steps and polite drafts
    |
SQLite local storage
```

## MVP Domains

Employment exit disputes:

- resignation and notice period
- employment bond and training cost recovery
- salary or full-and-final settlement withholding
- relieving letter issues
- non-compete, non-solicit, confidentiality
- arbitration and jurisdiction clauses

Tenant-landlord disputes:

- security deposit deduction
- eviction notice
- rent increase
- repairs and maintenance
- lock-in period
- notice period
- landlord harassment redirect and document withholding
- state/jurisdiction sensitivity

## MacBook Air M2-Friendly Design

- Python app, no Docker required.
- No GPU training.
- No Kubernetes or multi-container infrastructure.
- Default `LLM_PROVIDER=mock`, so no paid API key is required.
- Default `EMBEDDING_BACKEND=hash`, so the local demo does not download or initialize a model.
- Optional local MiniLM embeddings are available with `EMBEDDING_BACKEND=sentence-transformers` and `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`.
- Chroma is used when available, with a local JSON fallback for lightweight verification.

## Quickstart

```bash
cd /Users/pratyush/Coding/Projects/NyayaLens
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python scripts/ingest_sample_corpus.py
```

No API key is needed for the default local demo.

Equivalent Make commands:

```bash
make install
make ingest
```

## Run Backend

```bash
sh scripts/run_backend.sh
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Useful endpoints:

- `GET /health`
- `POST /upload`
- `POST /analyze`
- `POST /chat`
- `POST /corpus/ingest`
- `GET /corpus/status`
- `GET /analysis/{id}`

## Run Streamlit Frontend

```bash
streamlit run frontend/streamlit_app.py
```

The UI lets you upload a PDF, DOCX, or TXT, choose auto-detect or a dispute type, add context, and view a structured report.

## Analyze A Sample Document

```bash
python scripts/ingest_sample_corpus.py
streamlit run frontend/streamlit_app.py
```

In the UI, choose:

- `Sample employment contract`
- or `Sample rent agreement`

Then click `Analyze`.

Expected report sections:

- detected issue and domain
- extracted clauses and facts
- missing facts
- expert route
- retrieved sources
- rule checks
- risk flags
- uncertainty notes
- remedy plan
- safe draft message
- citation list
- audit trace

## Add Official Legal Sources

Place official PDFs, DOCX, or TXT files under:

```text
data/raw/laws/employment/
data/raw/laws/tenancy/
```

Then run:

```bash
python scripts/ingest_sample_corpus.py
```

The demo corpus starts with:

```text
DEMO CORPUS: This is a simplified educational placeholder. Replace with official legal sources before real-world use.
```

The app never claims that the corpus is complete.

## Local Mock Mode

The default `.env.example` is intentionally demo-safe:

```env
LLM_PROVIDER=mock
ALLOW_REMOTE_LLM=false
EMBEDDING_BACKEND=hash
```

In this mode, NyayaLens still demonstrates parsing, clause extraction, issue spotting, expert routing, local retrieval, deterministic rules, risk scoring, remedy planning, citations, and tests.

## Optional API LLM Mode

Mock mode is the default:

```env
LLM_PROVIDER=mock
ALLOW_REMOTE_LLM=false
```

To enable OpenAI-backed mode, set:

```env
OPENAI_API_KEY=...
LLM_PROVIDER=openai
ALLOW_REMOTE_LLM=true
```

Do not enable remote LLM mode for private documents unless the user explicitly accepts that document content may be sent to an API provider.

## Optional MiniLM Embeddings

For a stronger local vector representation, install/cache the small MiniLM model and set:

```env
EMBEDDING_BACKEND=sentence-transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

If the model is unavailable, NyayaLens falls back to deterministic hashing rather than requiring a download.

## Testing And Linting

```bash
python -m pytest
python -m ruff check .
```

Current test coverage includes clause extraction, issue spotting, employment rules, tenancy rules, unsafe refusal, retrieval citations, verifier checks, `/health`, and `/analyze`.

## Limitations

- Built-in sources are simplified demo placeholders.
- No official legal corpus is bundled.
- OCR is optional and reports a clear unavailable message if Tesseract is missing.
- The app does not provide legal advice, file cases, contact authorities, or guarantee outcomes.
- Exact legal section numbers are not generated unless they appear in retrieved source text.

## Roadmap

- Official public-source ingestion guide and source quality scoring.
- Citizen grievance routing.
- Farmer welfare disputes.
- Consumer rights.
- Legal aid routing by state.
- Multilingual support for Indian languages.
- Better evaluation set with annotated clauses and citations.

## Resume Bullets

- Built NyayaLens, an explainable legal-rights agent for Indian employment exit and tenancy disputes using FastAPI, Streamlit, LangGraph-compatible orchestration, SQLite, BM25, and Chroma-compatible retrieval.
- Implemented document parsing, clause extraction, MoE-style expert routing, local RAG, deterministic legal-risk rules, citation verification, safety guardrails, and mock-first LLM abstraction.
- Designed privacy-preserving mock mode that runs locally without paid APIs, local LLM downloads, or GPU training, with optional OpenAI integration behind explicit `ALLOW_REMOTE_LLM=true`.
- Added a lightweight retrieval path using BM25 plus deterministic embeddings by default, with optional MiniLM/Chroma support for stronger local semantic search.
- Added tests for extraction, issue classification, rules, retrieval, sample reports, verifier behavior, unsafe request refusal, and API endpoints.
