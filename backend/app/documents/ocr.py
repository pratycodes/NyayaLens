from __future__ import annotations

from pathlib import Path


def ocr_image_or_pdf(path: Path) -> tuple[str, list[str]]:
    """Optional OCR hook. The app works without Tesseract installed."""
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except Exception:
        return "", ["OCR unavailable: pytesseract/Pillow is not installed."]

    try:
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff"}:
            return pytesseract.image_to_string(Image.open(path)), []
    except Exception as exc:
        return "", [f"OCR failed: {exc}"]
    return "", ["OCR skipped: only image OCR is supported in this lightweight MVP."]
