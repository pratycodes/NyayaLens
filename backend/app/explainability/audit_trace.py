from __future__ import annotations

from datetime import datetime

from backend.app.core.schemas import AuditTraceEntry


def trace(
    node_name: str,
    input_summary: str,
    output_summary: str,
    warnings: list[str] | None = None,
    *,
    analysis_id: str | None = None,
    started_at: datetime | None = None,
    duration_ms: float = 0.0,
    error: str | None = None,
) -> AuditTraceEntry:
    started = started_at or datetime.utcnow()
    return AuditTraceEntry(
        analysis_id=analysis_id,
        node_name=node_name,
        started_at=started,
        duration_ms=duration_ms,
        input_summary=input_summary,
        output_summary=output_summary,
        warnings=warnings or [],
        error=error,
        timestamp=started,
    )
