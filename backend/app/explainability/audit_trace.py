from __future__ import annotations

from backend.app.core.schemas import AuditTraceEntry


def trace(node_name: str, input_summary: str, output_summary: str, warnings: list[str] | None = None) -> AuditTraceEntry:
    return AuditTraceEntry(
        node_name=node_name,
        input_summary=input_summary,
        output_summary=output_summary,
        warnings=warnings or [],
    )
