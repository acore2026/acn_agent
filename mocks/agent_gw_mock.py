from __future__ import annotations

import logging
import os
import sys
from typing import Any

import uvicorn
from fastapi import FastAPI, Request

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mocks.common import utc_now_iso

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | AgentGW Mock | %(message)s",
)
logger = logging.getLogger("agent_gw_mock")

app = FastAPI(title="AgentGW Mock", version="1.0.0")
STATE: dict[str, list[dict[str, Any]]] = {
    "agent_cards": [],
    "task_executions": [],
    "task_terminations": [],
}


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health endpoint."""
    return {"status": "ok", "service": "AgentGW Mock", "counts": {k: len(v) for k, v in STATE.items()}}


@app.post("/arf/v1/agent-cards")
async def agent_cards(request: Request) -> dict[str, Any]:
    """Mock AgentGW card query endpoint."""
    payload = await request.json()
    logger.info("收到agent-cards请求 body=%s", payload)
    STATE["agent_cards"].append(payload)
    return {
        "result": "success",
        "cards": [
            {
                "card_id": "agent-card-001",
                "agent_id": payload.get("agent_id"),
                "name": "AliceAgent",
                "priority": payload.get("priority", 2),
                "capabilities": ["inspection", "notification", "reporting"],
            }
        ],
        "processed_at": utc_now_iso(),
    }


@app.post("/acn-agent/v1/task-executions")
async def task_executions(request: Request) -> dict[str, Any]:
    """Mock AgentGW task execution endpoint."""
    payload = await request.json()
    logger.info("收到task-executions请求 body=%s", payload)
    STATE["task_executions"].append(payload)
    return {
        "result": "accepted",
        "task_id": payload.get("task_id"),
        "status": "running",
        "started_at": utc_now_iso(),
    }


@app.post("/acn-agent/v1/task-execution-terminations")
async def task_execution_terminations(request: Request) -> dict[str, Any]:
    """Mock AgentGW task termination endpoint."""
    payload = await request.json()
    logger.info("收到task-execution-terminations请求 body=%s", payload)
    STATE["task_terminations"].append(payload)
    return {
        "result": "success",
        "task_id": payload.get("task_id"),
        "status": "terminated",
        "processed_at": utc_now_iso(),
    }


@app.get("/mock/state")
async def mock_state() -> dict[str, Any]:
    """Return captured request state."""
    return STATE


def main() -> None:
    """Run AgentGW mock with python3 mocks/agent_gw_mock.py."""
    uvicorn.run(app, host="127.0.0.1", port=9001, log_level="info")


if __name__ == "__main__":
    main()
