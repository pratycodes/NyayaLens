# Resume Bullets

- Built NyayaLens, an evidence-grounded legal issue triage system for Indian employment, freelance-payment, and tenancy documents using FastAPI, Streamlit, SQLite, local retrieval, and deterministic rules.
- Implemented document parsing, clause extraction, issue-domain consistency checks, MoE-style expert routing, risk scoring, legal provision matching, verifier guardrails, and route-aware remedy generation.
- Designed a tabbed Streamlit report with key facts, risk tables, PDF evidence viewing, citation separation, law cross-references, trust metrics, export buttons, and audit/debug traces.
- Added privacy-preserving mock mode with lightweight hashing retrieval, optional MiniLM semantic retrieval, and optional OpenAI provider support behind explicit user consent.
- Built law-pack manifest validation and coverage reporting for official/demo/historical sources, including current BNS/BNSS/BSA handling and state tenancy law packs.
- Created a synthetic evaluation suite and public-safe demo artifacts covering false tenancy routes, false unsafe refusals, unpaid compensation, employment exit, tenant deposit, and unsafe request handling.
