# ruff: noqa: E402
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SAMPLE_DIR = ROOT / "data" / "raw" / "sample_uploads"
DEMO_FILES = [
    "demo_freelance_agreement.txt",
    "demo_employment_exit_agreement.txt",
    "demo_rent_agreement.txt",
]


def _write_pdf(text_path: Path) -> Path:
    import fitz  # type: ignore

    pdf_path = text_path.with_suffix(".pdf")
    pdf = fitz.open()
    page = pdf.new_page()
    y = 72
    for line in text_path.read_text(encoding="utf-8").splitlines():
        if y > 760:
            page = pdf.new_page()
            y = 72
        page.insert_text((72, y), line[:100], fontsize=10)
        y += 16
    pdf.save(pdf_path)
    pdf.close()
    return pdf_path


def main() -> int:
    outputs = [_write_pdf(SAMPLE_DIR / filename) for filename in DEMO_FILES]
    for output in outputs:
        print(f"Wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
