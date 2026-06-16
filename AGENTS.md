# NyayaLens Agent Instructions

## Project Goals
- Build a structured legal-rights analysis MVP for Indian employment exit and tenancy disputes.
- Keep the project practical on a MacBook Air M2: Python, FastAPI, Streamlit, SQLite, Chroma-compatible local retrieval, small embeddings, and optional API LLM calls only.
- The product flow is: upload document -> extract clauses -> detect issue -> route expert -> retrieve sources -> apply rules -> verify -> explain risk -> suggest safe next steps.

## Coding Standards
- Use type hints and Pydantic schemas for API and workflow boundaries.
- Keep functions small and deterministic where possible.
- Prefer local rules, templates, and retrieval over remote model calls for privacy.
- Do not add heavy infrastructure, local large LLMs, GPU training, Kubernetes, or multi-container requirements without explicit need.
- Keep tests meaningful and runnable with mock mode.

## Legal Safety Rules
- This project provides legal information, not legal advice.
- Do not fabricate laws, sections, portals, judgments, citations, or outcomes.
- Do not claim the demo corpus is complete.
- Exact legal provisions may be cited only when present in retrieved source text.
- If jurisdiction is unclear, say so and reduce confidence.
- Refuse unsafe requests involving forged evidence, threats, harassment, impersonation, illegal lock-breaking, blackmail, or bypassing lawful obligations.

## Privacy Rules
- Uploaded documents stay local.
- Do not send full document text to a remote LLM unless `ALLOW_REMOTE_LLM=true`.
- Default provider is `mock`.

## Required Verification
- Run `python -m pytest` before completion.
- Run `python -m ruff check .` or document why lint could not be run.
- Verify that sample employment and tenancy uploads produce extracted clauses, risk flags, citations, missing facts, remedy steps, and the legal-information disclaimer.
