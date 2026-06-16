# Official Corpus Guide

NyayaLens ships with simplified demo corpus files and a curated local official-law-pack area. Official packs are included only where a source file has been downloaded and validated against `data/raw/official/law_pack_manifest.json`; the project still does not claim complete legal coverage.

## Directory Layout

Place manually downloaded official/public files under:

```text
data/raw/official/
  contract/
  india_code/
  criminal/
  constitution/
  labour/
  tenancy/
  legal_aid/
  consumer/
  grievance/
```

Supported formats are PDF, DOCX, and TXT.

## Suggested Source Types

- India Code and Legislative Department materials
- Central and state labour department public guidance
- State rent/tenancy authority materials
- NALSA/DLSA legal aid resources
- Consumer and grievance public resources for future modules

Add the source URL and retrieval date in the file name or in a nearby README when curating a serious corpus. Do not copy restricted or non-public material.

## Starter Download List

For current criminal-law screening, manually download the official Ministry of Home Affairs PDFs into `data/raw/official/criminal/` and convert them into JSON law packs when section-level metadata is needed:

- Bharatiya Nyaya Sanhita, 2023: <https://www.mha.gov.in/sites/default/files/250883_english_01042024.pdf>
- Bharatiya Nagarik Suraksha Sanhita, 2023: <https://www.mha.gov.in/sites/default/files/250884_2_english_01042024.pdf>
- Bharatiya Sakshya Adhiniyam, 2023: <https://www.mha.gov.in/sites/default/files/250882_english_01042024.pdf>

For contract, constitution, labour, tenancy, and legal-aid coverage, download the relevant official India Code, Legislative Department, state department, and NALSA/DLSA public files into the matching folder. NyayaLens will load PDF/TXT/DOCX files, but curated JSON is preferred because it preserves act names, section numbers, issue tags, effective dates, and source authority.

Always verify the parsed title and Act number after download. The manifest validator rejects files whose parsed metadata does not match the expected Act name/domain so a wrongly named official PDF is not silently loaded under the wrong law pack.

## Current Tenancy Packs

The local tenancy folder currently includes official files for:

- Maharashtra Rent Control Act, 1999
- Karnataka Rent Act, 1999
- Delhi Rent Control Act, 1958
- Punjab Rent Act, 1995
- Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021
- West Bengal Premises Tenancy Act, 1997
- Rajasthan Rent Control Act, 2001
- Bihar Government Premises (Rent Recovery and Eviction) Act, 1956

Important caveats:

- Bihar coverage is limited. The ordinary private `Bihar Buildings (Lease, Rent and Eviction) Control Act, 1982` is listed in the manifest but remains `missing_official` until a verified official file is added.
- The Uttar Pradesh official PDF is mostly scanned. `up_urban_premises_tenancy_act_2021_ocr.txt` is an OCR-derived text file generated from the official India Code PDF so section-level search works without requiring OCR at runtime.
- State tenancy law is not pan-India complete. Add additional official state sources manually and check the coverage report before using a report outside demo evaluation.

## Ingestion

Demo only:

```bash
python scripts/ingest_corpus.py --corpus-mode demo
```

Official only:

```bash
python scripts/ingest_corpus.py --corpus-mode official
```

Demo plus official:

```bash
python scripts/ingest_corpus.py --corpus-mode mixed
```

The app surfaces corpus mode in the Overview and Evaluation / Trust tabs. If only demo material is retrieved, the report lowers trust and reminds the user to replace demo sources before real-world use.

## Section-Level Law Packs

The Law Cross-Reference tab reads law packs from:

```text
data/raw/official/contract/
data/raw/official/labour/
data/raw/official/criminal/
data/raw/official/constitution/
data/raw/official/tenancy/
data/raw/official/legal_aid/
```

Preferred format is JSON:

```json
{
  "pack_id": "official_contract_pack",
  "title": "Official Contract Law Pack",
  "corpus_mode": "official",
  "version_date": "YYYY-MM-DD",
  "sections": [
    {
      "act_name": "Act name",
      "act_id": "stable_act_id",
      "section_number": "section number",
      "section_title": "section title",
      "chapter": "chapter name",
      "text": "official source text excerpt",
      "jurisdiction": "India",
      "state": null,
      "domain": "contract_payment",
      "issue_tags": ["contract_payment"],
      "effective_from": "YYYY-MM-DD",
      "effective_to": null,
      "version_date": "YYYY-MM-DD",
      "source_authority": "India Code / Legislative Department",
      "source_url": "https://...",
      "corpus_mode": "official"
    }
  ]
}
```

TXT/PDF/DOCX files can also be placed in these folders. The loader will wrap each file as a user-supplied law section, but JSON is better for section-level metadata.

Run:

```bash
python scripts/ingest_law_packs.py
```

Generate section-level JSON packs from accepted official PDFs/TXT/DOCX files:

```bash
python scripts/generate_section_law_packs.py
python scripts/ingest_law_packs.py
```

Generated files are named like `generated_bns_2023_sections.json` and remain in the relevant law-pack folder. They preserve source metadata and improve the Law Cross-Reference tab from full-act matching toward section-level references.

This command validates `data/raw/official/law_pack_manifest.json`, rejects official files whose parsed metadata does not match the manifest, and writes:

```text
demo_outputs/law_pack_validation.json
demo_outputs/law_pack_coverage.json
```

To physically move rejected files out of active loading:

```bash
python scripts/ingest_law_packs.py --quarantine-mismatches
```

The default behavior is safer for review: mismatched files are rejected from official law-pack loading but are not moved.

## Manifest Validation

The manifest at `data/raw/official/law_pack_manifest.json` lists the expected title, optional Act number, domain, current/historical status, required official-mode flag, aliases, source authority, and known source filenames for each law pack.

Validation checks:

- expected title or aliases against parsed title
- expected Act number when a number can be parsed
- expected domain against inferred domain
- current versus historical status
- known filename expectations, such as the BSA filename

If a file is mismatched, NyayaLens marks it as `rejected_metadata_mismatch` and excludes it from official law-pack matches. Demo placeholders may still be available, but they do not replace official sources.

## Coverage Report

The Evaluation / Trust tab shows Official Law Pack Coverage with:

- Law pack
- Status
- Chunks
- Mode
- Notes

Statuses include `loaded_official`, `loaded_demo`, `missing_official`, `rejected_metadata_mismatch`, and `historical_loaded`. Missing official BSA is shown with:

```text
Official Bharatiya Sakshya Adhiniyam pack is missing; evidence-law cross-reference may be incomplete.
```

## Criminal-Law Date Rule

For current Indian criminal-law screening, use official packs for:

- Bharatiya Nyaya Sanhita, 2023
- Bharatiya Nagarik Suraksha Sanhita, 2023
- Bharatiya Sakshya Adhiniyam, 2023

Use IPC/CrPC/Evidence Act only as historical/pre-effective-date references for disputes before July 1, 2024.

## Citation Policy

NyayaLens should not fabricate laws, sections, portals, judgments, or outcomes. Exact legal provisions should appear only when present in retrieved source text. General deterministic rules must be labeled as general information.
