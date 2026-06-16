from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from backend.app.config import get_settings
from backend.app.core.schemas import FinalReport, model_to_dict
from backend.app.storage.models import StoredCorpusChunk


def get_connection(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or get_settings().sqlite_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS uploaded_documents (
                upload_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                content_type TEXT,
                size_bytes INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS analyses (
                analysis_id TEXT PRIMARY KEY,
                upload_id TEXT,
                filename TEXT,
                result_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS extracted_clauses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT NOT NULL,
                name TEXT NOT NULL,
                value TEXT,
                raw_text TEXT,
                page INTEGER,
                confidence TEXT,
                risk_hint TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_trace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                input_summary TEXT,
                output_summary TEXT,
                warnings_json TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS corpus_chunks (
                chunk_id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                source_file TEXT NOT NULL,
                domain TEXT,
                jurisdiction TEXT,
                document_type TEXT,
                title TEXT,
                page INTEGER,
                metadata_json TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def save_upload_metadata(
    *, upload_id: str, filename: str, path: Path, content_type: str | None, size_bytes: int | None
) -> None:
    initialize_database()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO uploaded_documents
            (upload_id, filename, path, content_type, size_bytes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (upload_id, filename, str(path), content_type, size_bytes),
        )


def get_upload_path(upload_id: str) -> Path | None:
    initialize_database()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT path FROM uploaded_documents WHERE upload_id = ?", (upload_id,)
        ).fetchone()
    return Path(row["path"]) if row else None


def save_analysis(report: FinalReport, *, upload_id: str | None = None, filename: str | None = None) -> None:
    initialize_database()
    payload = model_to_dict(report)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO analyses (analysis_id, upload_id, filename, result_json)
            VALUES (?, ?, ?, ?)
            """,
            (report.analysis_id, upload_id, filename, json.dumps(payload)),
        )
        conn.execute("DELETE FROM extracted_clauses WHERE analysis_id = ?", (report.analysis_id,))
        conn.execute("DELETE FROM audit_trace WHERE analysis_id = ?", (report.analysis_id,))
        for clause in report.extracted_facts.extracted_clauses:
            conn.execute(
                """
                INSERT INTO extracted_clauses
                (analysis_id, name, value, raw_text, page, confidence, risk_hint)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.analysis_id,
                    clause.name,
                    clause.value,
                    clause.raw_text,
                    clause.page,
                    clause.confidence,
                    clause.risk_hint,
                ),
            )
        for entry in report.audit_trace:
            conn.execute(
                """
                INSERT INTO audit_trace
                (analysis_id, node_name, input_summary, output_summary, warnings_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    report.analysis_id,
                    entry.node_name,
                    entry.input_summary,
                    entry.output_summary,
                    json.dumps(entry.warnings),
                    entry.timestamp.isoformat(),
                ),
            )


def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    initialize_database()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT result_json FROM analyses WHERE analysis_id = ?", (analysis_id,)
        ).fetchone()
    return json.loads(row["result_json"]) if row else None


def save_corpus_chunks(chunks: list[StoredCorpusChunk]) -> None:
    initialize_database()
    with get_connection() as conn:
        for chunk in chunks:
            conn.execute(
                """
                INSERT OR REPLACE INTO corpus_chunks
                (chunk_id, text, source_file, domain, jurisdiction, document_type, title, page, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.chunk_id,
                    chunk.text,
                    chunk.source_file,
                    chunk.domain,
                    chunk.jurisdiction,
                    chunk.document_type,
                    chunk.title,
                    chunk.page,
                    json.dumps(
                        {
                            "source_file": chunk.source_file,
                            "domain": chunk.domain,
                            "jurisdiction": chunk.jurisdiction,
                            "document_type": chunk.document_type,
                            "title": chunk.title,
                            "page": chunk.page,
                            "chunk_id": chunk.chunk_id,
                        }
                    ),
                ),
            )


def load_corpus_chunks() -> list[StoredCorpusChunk]:
    initialize_database()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT chunk_id, text, source_file, domain, jurisdiction, document_type, title, page
            FROM corpus_chunks
            ORDER BY source_file, chunk_id
            """
        ).fetchall()
    return [
        StoredCorpusChunk(
            chunk_id=row["chunk_id"],
            text=row["text"],
            source_file=row["source_file"],
            domain=row["domain"] or "general",
            jurisdiction=row["jurisdiction"] or "India",
            document_type=row["document_type"] or "general_information",
            title=row["title"] or row["source_file"],
            page=row["page"],
        )
        for row in rows
    ]


def corpus_status() -> tuple[int, list[str]]:
    chunks = load_corpus_chunks()
    return len(chunks), sorted({chunk.source_file for chunk in chunks})
