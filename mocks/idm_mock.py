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
    format="%(asctime)s | %(levelname)s | IDM Mock | %(message)s",
)
logger = logging.getLogger("idm_mock")

app = FastAPI(title="IDM Mock", version="1.0.0")
STATE: dict[str, list[dict[str, Any]]] = {
    "identity_applications": [],
    "agent_deletions": [],
}


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health endpoint."""
    return {"status": "ok", "service": "IDM Mock", "counts": {k: len(v) for k, v in STATE.items()}}


@app.post("/idm/v1/identity-applications")
async def identity_applications(request: Request) -> dict[str, Any]:
    """Mock IDM identity application endpoint."""
    payload = await request.json()
    logger.info("收到身份申请请求 body=%s", payload)
    STATE["identity_applications"].append(payload)
    return {
        "result": "success",
        "agent_id": "did:acn:agent:987654321",
        "issued_at": utc_now_iso(),
        "echo": payload,
        "vc0": {
            "context": ["3gpp-ts-33.xxx-v20.0.0"],
            "id": "CMCC/credentials/3732",
            "type": ["VerifiableCredential", "BindingSIMCredential"],
            "issuer": "did:udid:NewTypeOperator",
            "valid_from": "2010-01-01T19:23:24Z",
            "valid_until": "2035-01-01T19:23:24Z",
            "claims": {
                "agent_name": payload.get("name", "UnknownAgent"),
                "agent_id": "did:acn:agent:987654321",
                "agent_attribute": "运营商颁发的Agent绑定凭证",
            },
            "proof": {
                "creator": "did:udid:NewTypeOperator#keys-1",
                "signature_value": "idm-mock-signature",
            },
        },
    }


@app.post("/acn-agent/v1/agent-deletions")
async def agent_deletions(request: Request) -> dict[str, Any]:
    """Mock IDM agent deletion endpoint."""
    payload = await request.json()
    logger.info("收到Agent删除请求 body=%s", payload)
    STATE["agent_deletions"].append(payload)
    return {
        "result": "success",
        "message": "Agent deletion accepted by IDM mock",
        "deleted_agent_id": payload.get("agent_id"),
        "processed_at": utc_now_iso(),
    }


@app.get("/mock/state")
async def mock_state() -> dict[str, Any]:
    """Return captured request state."""
    return STATE


def main() -> None:
    """Run IDM mock with python3 mocks/idm_mock.py."""
    uvicorn.run(app, host="127.0.0.1", port=9020, log_level="info")


if __name__ == "__main__":
    main()
