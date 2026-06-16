from __future__ import annotations

from fastapi import APIRouter

from backend.app.config import get_settings
from backend.app.storage.sqlite import initialize_database

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    initialize_database()
    settings = get_settings()
    return {
        "status": "ok",
        "app": "NyayaLens",
        "env": settings.app_env,
        "llm_provider": settings.llm_provider,
    }
