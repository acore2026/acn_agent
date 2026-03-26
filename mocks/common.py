from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class MockPorts:
    """Port constants used by local mock services."""

    agent: int = 9010
    idm: int = 9020
    agent_gw: int = 9001
    webui: int = 9005


LOCAL_HOST = "127.0.0.1"
PORTS = MockPorts()


def utc_now_iso() -> str:
    """Return a UTC ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def build_url(port: int, path: str) -> str:
    """Build a local HTTP URL."""
    return f"http://{LOCAL_HOST}:{port}{path}"


def sample_identity_application() -> dict[str, Any]:
    """Sample IDM identity application message."""
    return {
        "owner": "demo-owner",
        "name": "AliceAgent",
        "public_key": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A-demo",
        "description": "AgentModel-X, SN123456",
        "timestamp": 1711185600,
        "signature": "demo-signature",
        "signature_encoding": "base64",
        "metadata": {
            "region": "CN",
            "os": "Linux",
            "version": "1.0.0",
        },
    }


def sample_agent_cards_request() -> dict[str, Any]:
    """Sample AgentGW agent card request."""
    return {
        "agent_id": "did:acn:agent:987654321",
        "priority": 2,
        "timestamp": "2024-03-23T12:00:00Z",
        "signature": "base64_encoded_signature_string",
        "vc_list": [
            {
                "context": ["3gpp-ts-33.xxx-v20.0.0"],
                "id": "CMCC/credentials/3732",
                "type": ["VerifiableCredential", "BindingSIMCredential"],
                "issuer": "did:udid:NewTypeOperator",
                "valid_from": "2010-01-01T19:23:24Z",
                "valid_until": "2020-01-01T19:23:24Z",
                "claims": {
                    "agent_name": "AliceAgent",
                    "agent_id": "did:acn:agent:987654321",
                    "agent_attribute": "6G业务通信",
                    "authorization_mode": "Mode2",
                },
                "proof": {
                    "creator": "did:udid:NewTypeOperator#keys-1",
                    "signature_value": "uill9900",
                },
            }
        ],
    }


def sample_task_execution() -> dict[str, Any]:
    """Sample task execution message."""
    return {
        "agent_id": "did:acn:agent:987654321",
        "task_id": "task-12345",
        "description": "危险区域巡检任务",
        "timestamp": "2024-03-23T12:00:00Z",
    }


def sample_agent_deletion() -> dict[str, Any]:
    """Sample agent deletion message."""
    return {
        "agent_id": "did:acn:agent:987654321",
        "reason": "retired",
        "timestamp": "2024-03-23T12:00:00Z",
        "signature": "demo-delete-signature",
        "signature_encoding": "base64",
    }


def sample_task_termination() -> dict[str, Any]:
    """Sample task termination message."""
    return {
        "task_id": "task-12345",
        "agent_id": "did:acn:agent:987654321",
        "reason": "目标对象离开监控区域",
        "timestamp": "2024-03-23T12:00:00Z",
        "force": False,
    }
