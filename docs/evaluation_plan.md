# Evaluation Plan

## Clause Extraction

Metric: clause-level precision, recall, and F1.

Targets:

- notice period
- bond amount
- training cost
- non-compete duration
- salary withholding
- deposit
- lock-in
- eviction
- jurisdiction
- arbitration

## Issue Classification

Metric: accuracy and macro F1 across MVP issue types.

Test sets should include short dispute descriptions and full agreements.

## Retrieval

Metric: precision@k and citation relevance.

Each answer should cite chunks that support the risk explanation.

## Citation Accuracy

Metric: percentage of legal claims supported by retrieved sources.

Verifier failures should be reviewed manually.

## Hallucination Rate

Metric: unsupported exact sections, invented portals, invented judgments, or overclaimed outcomes per report.

Target: zero in mock mode.

## Abstention Accuracy

Metric: whether the system lowers confidence or says it lacks enough verified material when sources or jurisdiction are missing.

## Remedy Usefulness

Metric: human rating for practicality, safety, clarity, and evidence completeness.

## Safety Refusal Tests

The test suite should include prompts about threats, forged evidence, blackmail, impersonation, lock-breaking, and unlawful self-help actions. Expected output is refusal plus lawful alternatives.

## Deterministic Scenario Suite

Run:

```bash
python scripts/run_eval.py
```

The scenario file is `eval/scenarios.json` and contains synthetic cases across:

- freelance payment and service agreement review
- employment exit, bond, notice, non-compete, and unpaid settlement
- tenant deposit, eviction, rent increase, repair, and lock-in disputes
- unsafe harmful requests
- victim/reporting contexts that should not be refused
- document-domain confusion cases such as TDS deduction and generic damages language

The script writes:

```text
demo_outputs/eval_summary.json
demo_outputs/eval_summary.md
```

Reported metrics include document type accuracy, issue classification accuracy, domain accuracy, primary expert accuracy, citation coverage, false unsafe refusal rate, unsafe request refusal rate, false tenancy route rate, remedy language correctness, and missing facts relevance.
