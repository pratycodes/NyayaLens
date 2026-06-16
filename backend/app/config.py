from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    app_env: str = "dev"
    log_level: str = "INFO"
    openai_api_key: str = ""
    llm_provider: str = "mock"
    allow_remote_llm: bool = False
    embedding_backend: str = "hash"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_persist_dir: Path = ROOT_DIR / "data" / "vectorstore" / "chroma"
    sqlite_path: Path = ROOT_DIR / "data" / "sqlite" / "nyayalens.db"
    raw_laws_dir: Path = ROOT_DIR / "data" / "raw" / "laws"
    processed_dir: Path = ROOT_DIR / "data" / "processed"
    sample_uploads_dir: Path = ROOT_DIR / "data" / "raw" / "sample_uploads"


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    settings = Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        allow_remote_llm=_bool(os.getenv("ALLOW_REMOTE_LLM"), False),
        embedding_backend=os.getenv("EMBEDDING_BACKEND", "hash"),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        chroma_persist_dir=Path(
            os.getenv("CHROMA_PERSIST_DIR", ROOT_DIR / "data" / "vectorstore" / "chroma")
        ),
        sqlite_path=Path(os.getenv("SQLITE_PATH", ROOT_DIR / "data" / "sqlite" / "nyayalens.db")),
    )
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    return settings
