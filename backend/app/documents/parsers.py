from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.core.errors import UnsupportedDocumentError


@dataclass
class ParsedDocument:
    text: str
    page_texts: list[tuple[int, str]]
    warnings: list[str]


def parse_txt(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return ParsedDocument(text=text, page_texts=[(1, text)], warnings=[])


def parse_docx(path: Path) -> ParsedDocument:
    try:
        from docx import Document  # type: ignore
    except Exception as exc:
        raise UnsupportedDocumentError("python-docx is required for DOCX parsing.") from exc
    document = Document(path)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs)
    return ParsedDocument(text=text, page_texts=[(1, text)], warnings=[])


def _parse_pdf_pymupdf(path: Path) -> ParsedDocument:
    import fitz  # type: ignore

    page_texts: list[tuple[int, str]] = []
    warnings: list[str] = []
    with fitz.open(path) as pdf:
        for index, page in enumerate(pdf, start=1):
            page_text = page.get_text("text") or ""
            if not page_text.strip():
                warnings.append(f"Page {index} had no extractable text.")
            page_texts.append((index, page_text))
    return ParsedDocument(
        text="\n".join(page_text for _, page_text in page_texts),
        page_texts=page_texts,
        warnings=warnings,
    )


def _parse_pdf_pdfplumber(path: Path) -> ParsedDocument:
    import pdfplumber  # type: ignore

    page_texts: list[tuple[int, str]] = []
    warnings: list[str] = ["PyMuPDF failed; used pdfplumber fallback."]
    with pdfplumber.open(path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            if not page_text.strip():
                warnings.append(f"Page {index} had no extractable text.")
            page_texts.append((index, page_text))
    return ParsedDocument(
        text="\n".join(page_text for _, page_text in page_texts),
        page_texts=page_texts,
        warnings=warnings,
    )


def parse_pdf(path: Path) -> ParsedDocument:
    try:
        return _parse_pdf_pymupdf(path)
    except Exception:
        try:
            return _parse_pdf_pdfplumber(path)
        except Exception as exc:
            raise UnsupportedDocumentError(
                "PDF parsing failed with PyMuPDF and pdfplumber. OCR may be required."
            ) from exc


def parse_document(path: Path) -> ParsedDocument:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return parse_txt(path)
    if suffix == ".docx":
        return parse_docx(path)
    if suffix == ".pdf":
        return parse_pdf(path)
    raise UnsupportedDocumentError(f"Unsupported file type: {suffix or 'unknown'}")
