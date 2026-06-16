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
    4. issue-domain consistency checks
    5. route_jurisdiction
    6. route_expert
    7. retrieve_sources
    8. apply_rules
    9. build_explanation
   10. route_remedy
   11. verify_answer
   12. safety_finalize
   13. report view model
    |
Tabbed structured report with citations, risk flags, PDF evidence, remedy plan, trust panel, and audit trace
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
- `UnpaidCompensationExpert`
- `EmploymentCompensationExpert`
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

## Issue-Domain Consistency

`backend/app/agents/issue_domain_consistency.py` prevents common public-demo failures:

- TDS deduction in a freelance agreement is not a tenancy security deposit issue.
- Generic contract damages/injunctive-relief language is not a repair dispute.
- Harassment text in uploaded documents or corpus chunks is not treated as unsafe user intent.
- Freelance/service agreements do not route to tenancy without strong tenancy indicators.

Safety blocking only inspects active user intent, not uploaded documents or retrieved sources.

## Report View Model And UI

`backend/app/explainability/report_view_model.py` transforms the raw `FinalReport` into UI-ready tables and citations:

- summary cards
- key facts table
- risk table
- important sections
- uploaded document citations
- legal/demo corpus citations
- counterparty arguments
- trust panel
- debug payload

The Streamlit UI consumes this view model across Overview, Risks & Remedies, Document Review, Sources & Citations, Drafts & Checklist, Evaluation / Trust, and Audit / Debug tabs.

## Law Cross-Reference

`backend/app/law_packs/` loads section-level law-pack metadata from `data/raw/official/`.

`backend/app/legal_ontology/` maps issue types to legal areas such as contract payment, labour classification, tenancy deposit, criminal screening, and constitution/public law.

`backend/app/legal_matcher/` ranks potentially relevant provisions and applies safety filters:

- BNS/BSA/BNSS markers are preferred for criminal screening on or after July 1, 2024.
- IPC-style historical markers are used only before July 1, 2024.
- Criminal screening requires facts such as forgery, threats, blackmail, dishonest inducement, theft, misappropriation, or fraud.
- Constitution/public-law matching requires government/public authority, public official, state action, statutory authority, public benefit, or grievance context.
- Ordinary private freelance/company payment disputes map to contract/payment first.

The output uses cautious labels such as potentially relevant provision, possible civil breach, possible statutory non-compliance, possible criminal allegation, and not enough facts.

## Local Storage

SQLite stores:

- uploaded document metadata
- analysis result JSON
- extracted clauses
- audit trace entries
- corpus chunk metadata

Uploaded documents remain local.
