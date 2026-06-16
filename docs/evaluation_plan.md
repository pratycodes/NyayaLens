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
