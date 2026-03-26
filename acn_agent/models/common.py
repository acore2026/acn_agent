from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).isoformat()


class PipelineLog(BaseModel):
    """Pipeline log message sent to WebUI."""

    source: str
    destination: str
    timestamp: str = Field(default_factory=utc_now_iso)
    task_id: str | None = None
    protocol: str = "HTTP"
    headers: dict[str, Any] | str = Field(default_factory=dict)
    abstract: str = ""
    content: Any = Field(default_factory=dict)


class ProxyRecord(BaseModel):
    """In-memory audit record for a forwarded message."""

    path: str
    upstream_name: str
    upstream_url: str
    request_body: dict[str, Any]
    response_status: int
    response_body: Any
    created_at: str = Field(default_factory=utc_now_iso)


class ClearResponse(BaseModel):
    """Response returned after WebUI clear request."""

    result: str = "success"
    message: str
    cleared_records: int
    cleared_pipeline_logs: int
