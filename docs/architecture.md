# Architecture

NyayaLens is a structured legal-rights analysis system. It is designed to organize a user's document and facts before producing a conservative risk report.

## Workflow

```text
User upload or text
    |
Streamlit UI or FastAPI
    |
Analysis workflow
    |
    1. parse_document
    2. extract_clauses
    3. spot_issue
    4. route_jurisdiction
    5. route_expert
    6. retrieve_sources
    7. apply_rules
    8. build_explanation
    9. plan_remedy
   10. verify_answer
   11. safety_finalize
    |
Structured report with citations, risk flags, remedy plan, and audit trace
```

The workflow is implemented as named node functions in `backend/app/agents/graph.py`. When `langgraph` is installed, `build_langgraph_app()` compiles the same nodes into a `StateGraph`. If LangGraph is unavailable, the nodes run sequentially so mock mode remains lightweight.

## MoE-Style Routing

The expert router returns:

- `primary_expert`
- `secondary_experts`
- `confidence`
- `route_reason`

Current experts:

- `EmploymentExitExpert`
- `TenancyExpert`
- `ContractClauseExpert`
- `LegalAidSafetyExpert`
- `VerifierExpert`

Routing is deterministic in mock mode. It uses the issue domain, issue type, and safety state rather than a free-form chatbot response.

## RAG + Rules + Verifier

Retrieval provides relevant source excerpts from local files under `data/raw/laws/`. It uses BM25 and a Chroma-compatible vector store with deterministic fallback embeddings.

Rules inspect extracted facts and context. They produce `RuleResult` and `RiskFlag` records with triggering evidence and suggested next steps.

The verifier checks:

- legal information disclaimer is present
- exact legal section claims have citation support
- jurisdiction is not overclaimed
- unsafe requests are refused
- missing facts are listed
- outcomes are not guaranteed

## Local Storage

SQLite stores:

- uploaded document metadata
- analysis result JSON
- extracted clauses
- audit trace entries
- corpus chunk metadata

Uploaded documents remain local.
