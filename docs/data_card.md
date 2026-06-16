# Data Card

## Corpus Type

NyayaLens ships with a small demo corpus for development and testing. Each source begins with:

```text
DEMO CORPUS: This is a simplified educational placeholder. Replace with official legal sources before real-world use.
```

## Included Demo Files

- `data/raw/laws/employment/employment_general_information.txt`
- `data/raw/laws/employment/contract_general_information.txt`
- `data/raw/laws/tenancy/tenancy_general_information.txt`
- `data/raw/laws/tenancy/legal_aid_general_information.txt`

## Intended Use

The demo corpus is for showing ingestion, retrieval, citations, rule checks, and verifier behavior. It is not a complete or authoritative statement of Indian law.

## Replacing With Official Sources

Add official public legal materials manually under:

```text
data/raw/laws/employment/
data/raw/laws/tenancy/
```

Supported formats:

- TXT
- PDF
- DOCX

Run:

```bash
python scripts/ingest_sample_corpus.py
```

## Metadata

Ingestion attaches:

- source file
- domain
- jurisdiction
- document type
- title
- page number when available
- chunk id

## Limitations

- Demo sources are simplified.
- Official source freshness is the user's responsibility.
- State-specific tenancy and employment rules require official state materials.
- The system should abstain or lower confidence when retrieval does not support a claim.
