from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.agents.graph import run_analysis
from backend.app.core.schemas import AnalyzeRequest, AnalyzeResponse
from backend.app.documents.parsers import parse_document
from backend.app.storage.sqlite import get_analysis, get_upload_path

router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        text = request.text
        page_texts = [(1, request.text or "")]
        warnings: list[str] = []
        filename = request.filename
        if request.upload_id:
            path = get_upload_path(request.upload_id)
            if path is None:
                raise HTTPException(status_code=404, detail="upload_id not found")
            parsed = parse_document(path)
            text = parsed.text
            page_texts = parsed.page_texts
            warnings = parsed.warnings
            filename = path.name
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Provide text or a valid upload_id.")
        report = run_analysis(
            text=text,
            context=request.context,
            filename=filename,
            page_texts=page_texts,
            parser_warnings=warnings,
            upload_id=request.upload_id,
            persist=True,
        )
        return AnalyzeResponse(report=report)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/analysis/{analysis_id}")
def get_analysis_result(analysis_id: str) -> dict:
    result = get_analysis(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail="analysis_id not found")
    return result
