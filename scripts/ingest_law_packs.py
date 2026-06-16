# ruff: noqa: E402
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.law_packs.coverage import write_law_pack_coverage_report
from backend.app.law_packs.ingest_law_pack import ingest_law_packs
from backend.app.law_packs.law_pack_loader import clear_law_pack_cache, law_pack_status
from backend.app.law_packs.registry import ensure_law_pack_folders
from backend.app.law_packs.validation import (
    quarantine_mismatched_files,
    validate_law_pack_files,
    write_law_pack_validation_report,
)

CURRENT_CRIMINAL_ACTS = {
    "Bharatiya Nyaya Sanhita, 2023",
    "Bharatiya Nagarik Suraksha Sanhita, 2023",
    "Bharatiya Sakshya Adhiniyam, 2023",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and load local law packs.")
    parser.add_argument(
        "--quarantine-mismatches",
        action="store_true",
        help="Move rejected official files into data/raw/official/_quarantine/ before loading.",
    )
    args = parser.parse_args()

    ensure_law_pack_folders()
    if args.quarantine_mismatches:
        moved = quarantine_mismatched_files()
        clear_law_pack_cache()
        if moved:
            print("Quarantined mismatched law-pack files:")
            for path in moved:
                print(f"- {path}")

    validation_path = write_law_pack_validation_report()
    validation = validate_law_pack_files()
    sections = ingest_law_packs()
    status = law_pack_status()
    coverage_path = write_law_pack_coverage_report()
    print(f"Loaded {len(sections)} law-pack sections from {status.pack_count} packs.")
    for pack in status.law_packs_loaded:
        print(f"- {pack}")
    print(f"\nValidation report: {validation_path.relative_to(ROOT)}")
    print(f"Coverage report: {coverage_path.relative_to(ROOT)}")
    official_current = {section.act_name for section in sections if section.corpus_mode == "official"}
    missing_current = sorted(CURRENT_CRIMINAL_ACTS - official_current)
    if missing_current:
        print("\nMissing official current criminal-law packs:")
        for act_name in missing_current:
            print(f"- {act_name}")
        print("Demo placeholders may still be present, but official files should replace them.")
    if validation.rejected_files:
        print("\nRejected law-pack files:")
        for item in validation.rejected_files:
            print(f"- {item.source_file}: expected {item.expected_title}, parsed {item.parsed_title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
