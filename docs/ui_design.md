# UI Design

NyayaLens is designed as a structured legal issue triage and document review system, not a chatbot.

## Report Tabs

1. Overview: summary cards and a concise key facts table.
2. Risks & Remedies: filterable risk table and possible counterparty arguments.
3. Document Review: uploaded-document evidence viewer with important sections.
4. Sources & Citations: uploaded-document citations separated from local corpus citations.
5. Law Cross-Reference: potentially relevant law-pack provisions, missing facts, implication level, citations, and human-review flag.
6. Drafts & Checklist: safe next steps, evidence checklist, and copyable draft.
7. Evaluation / Trust: confidence explanation, corpus mode, retrieval mode, law-pack coverage, missing facts, human review, safety, and citation coverage.
8. Audit / Debug: raw clauses, enums, retrieval scores, rule checks, verifier result, provision matches, audit trace, and raw JSON.

## Progressive Disclosure

The main UI shows the shortest useful explanation first. Raw clauses, duplicate occurrences, retrieval scores, and audit internals are intentionally hidden in Audit / Debug.

## Citation Behavior

Every major key fact and risk row should connect to one of:

- uploaded document citation
- legal/demo corpus citation
- deterministic-general-information label

Law cross-reference rows should connect to law-pack citations and should not say that a law is broken or that a violation is proven.

For PDFs, the Document Review tab renders pages locally with PyMuPDF and highlights a selected quote when text search succeeds. If exact highlighting fails, it shows the cited page and extracted quote.

## Domain-Specific Tone

Freelance/service payment reports use company/client/accounts language. HR/payroll wording is used only for employee or employment-contract contexts. Tenancy reports use landlord/deposit/notice language.
