from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from backend.app.config import get_settings
from backend.app.documents.parsers import ParsedDocument, parse_document


def save_upload_file(file: UploadFile) -> tuple[str, Path]:
    settings = get_settings()
    upload_id = str(uuid.uuid4())
    suffix = Path(file.filename or "upload.txt").suffix or ".txt"
    safe_name = f"{upload_id}{suffix.lower()}"
    upload_dir = settings.processed_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / safe_name
    content = file.file.read()
    destination.write_bytes(content)
    return upload_id, destination


def load_uploaded_document(path: Path) -> ParsedDocument:
    return parse_document(path)
