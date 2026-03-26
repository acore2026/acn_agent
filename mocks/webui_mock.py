from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | WebUI Mock | %(message)s",
)
logger = logging.getLogger("webui_mock")

app = FastAPI(title="WebUI Mock", version="1.0.0")
PIPELINE_LOGS: list[dict[str, Any]] = []


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health endpoint."""
    return {"status": "ok", "service": "WebUI Mock", "pipeline_log_count": len(PIPELINE_LOGS)}


@app.post("/acn/v3/pipeline-logs")
async def pipeline_logs(request: Request) -> dict[str, Any]:
    """Receive pipeline logs from ACN Agent."""
    payload = await request.json()
    logger.info("收到pipeline-log body=%s", payload)
    PIPELINE_LOGS.append(payload)
    return {
        "result": "success",
        "message": "pipeline log stored",
        "stored_count": len(PIPELINE_LOGS),
    }


@app.get("/mock/pipeline-logs")
async def get_pipeline_logs() -> dict[str, Any]:
    """Inspect stored pipeline logs."""
    return {"count": len(PIPELINE_LOGS), "items": PIPELINE_LOGS}


@app.delete("/mock/pipeline-logs")
async def clear_pipeline_logs() -> dict[str, Any]:
    """Clear stored pipeline logs."""
    count = len(PIPELINE_LOGS)
    PIPELINE_LOGS.clear()
    return {"result": "success", "cleared": count}
