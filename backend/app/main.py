from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes_analyze import router as analyze_router
from backend.app.api.routes_chat import router as chat_router
from backend.app.api.routes_corpus import router as corpus_router
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_upload import router as upload_router
from backend.app.config import get_settings
from backend.app.corpus.sample_corpus import ensure_sample_corpus
from backend.app.logging_config import configure_logging
from backend.app.storage.sqlite import initialize_database


def create_app() -> FastAPI:
    configure_logging()
    initialize_database()
    ensure_sample_corpus()
    settings = get_settings()
    app = FastAPI(
        title="NyayaLens",
        description="Explainable Legal-Rights Agent for Indian Employment Exit and Tenancy Disputes",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(upload_router)
    app.include_router(analyze_router)
    app.include_router(chat_router)
    app.include_router(corpus_router)
    return app


app = create_app()
