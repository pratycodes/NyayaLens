from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from starlette.datastructures import UploadFile

from backend.app.config import get_settings
from backend.app.core.schemas import UploadResponse
from backend.app.documents.loaders import load_uploaded_document
from backend.app.storage.sqlite import save_upload_metadata

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(request: Request) -> UploadResponse:
    try:
        form = await request.form()
        file = form.get("file")
        if not isinstance(file, UploadFile):
            raise HTTPException(status_code=400, detail="Expected multipart field named 'file'.")
        settings = get_settings()
        upload_id = str(uuid.uuid4())
        suffix = Path(file.filename or "upload.txt").suffix or ".txt"
        path = settings.processed_dir / "uploads" / f"{upload_id}{suffix.lower()}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(await file.read())
        parsed = load_uploaded_document(path)
        save_upload_metadata(
            upload_id=upload_id,
            filename=file.filename or path.name,
            path=path,
            content_type=file.content_type,
            size_bytes=path.stat().st_size,
        )
        return UploadResponse(
            upload_id=upload_id,
            filename=file.filename or path.name,
            parser_warnings=parsed.warnings,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
