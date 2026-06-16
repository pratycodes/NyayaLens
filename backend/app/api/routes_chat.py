from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.agents.safety_guardrails import SAFE_REFUSAL, detect_unsafe_request
from backend.app.core.constants import LEGAL_DISCLAIMER
from backend.app.storage.sqlite import get_analysis

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    analysis_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    disclaimer: str = LEGAL_DISCLAIMER


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    analysis = get_analysis(request.analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="analysis_id not found")
    unsafe, _matches = detect_unsafe_request(request.question)
    if unsafe:
        return ChatResponse(answer=SAFE_REFUSAL)
    missing = ", ".join(analysis.get("missing_facts", [])[:6]) or "none listed"
    return ChatResponse(
        answer=(
            "Based on the existing structured report, keep follow-up questions tied to the cited sources, "
            f"missing facts ({missing}), and the evidence checklist. I cannot provide legal advice or guarantee outcomes."
        )
    )
