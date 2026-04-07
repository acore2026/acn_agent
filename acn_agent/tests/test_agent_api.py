from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from acn_agent.core.config import Settings
from acn_agent.main import create_app


class RecordingTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.requests: list[tuple[str, dict[str, Any]]] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        body = await request.aread()
        payload = {}
        if body:
            payload = json.loads(body.decode())
        self.requests.append((str(request.url), payload))

        if request.url.path == "/acn/v3/pipeline-logs":
            return httpx.Response(status_code=200, json={"result": "logged"})
        if request.url.path == "/idm/v1/identity-applications":
            return httpx.Response(status_code=200, json={"result": "success", "agent_id": "did:acn:test:1"})
        if request.url.path == "/acn-agent/v1/agent-deletions":
            return httpx.Response(status_code=200, json={"result": "deleted"})
        if request.url.path == "/arf/v1/agent-cards":
            return httpx.Response(status_code=200, json={"result": "success", "cards": ["card-1"]})
        if request.url.path == "/acn-agent/v1/task-executions":
            return httpx.Response(status_code=202, json={"result": "accepted", "task_id": payload.get("task_id")})
        if request.url.path == "/acn-agent/v1/task-execution-terminations":
            return httpx.Response(status_code=200, json={"result": "terminated"})
        return httpx.Response(status_code=404, json={"detail": "not found"})


@pytest.fixture()
def test_app(tmp_path: Path) -> tuple[Any, RecordingTransport]:
    transport = RecordingTransport()
    settings = Settings(
        idm_host="idm.local",
        agent_gw_host="agentgw.local",
        webui_host="webui.local",
        agent_db_path=str(tmp_path / "acn_agent_test.db"),
    )
    app = create_app(settings=settings, transport=transport)
    return app, transport


async def post_json(app: Any, path: str, payload: dict[str, Any]) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        return await client.post(path, json=payload)


async def get_json(app: Any, path: str) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        return await client.get(path)


def test_identity_applications_route(test_app: tuple[Any, RecordingTransport]) -> None:
    app, transport = test_app
    response = asyncio.run(
        post_json(
            app,
            "/idm/v1/identity-applications",
            {"owner": "alice", "name": "AliceAgent", "description": "AgentModel-X, SN123456"},
        )
    )
    assert response.status_code == 200
    assert response.json()["agent_id"] == "did:acn:test:1"
    assert any(url == "http://idm.local:9020/idm/v1/identity-applications" for url, _ in transport.requests)

    owner_response = asyncio.run(post_json(app, "/acn-agent/v1/owner-agents", {"owner": "alice"}))
    assert owner_response.status_code == 200
    assert owner_response.json() == {
        "owner": "alice",
        "total": 1,
        "agents": [
            {
                "agent_id": "did:acn:test:1",
                "agent_name": "AliceAgent",
                "description": "AgentModel-X, SN123456",
            }
        ],
    }


def test_agent_gw_routes(test_app: tuple[Any, RecordingTransport]) -> None:
    app, transport = test_app
    cards_response = asyncio.run(post_json(app, "/arf/v1/agent-cards", {"agent_id": "a-1"}))
    exec_response = asyncio.run(post_json(app, "/acn-agent/v1/task-executions", {"agent_id": "a-1", "task_id": "task-1"}))
    termination_response = asyncio.run(
        post_json(app, "/acn-agent/v1/task-execution-terminations", {"agent_id": "a-1", "task_id": "task-1"})
    )

    assert cards_response.status_code == 200
    assert exec_response.status_code == 202
    assert termination_response.status_code == 200
    assert any(url == "http://agentgw.local:9001/arf/v1/agent-cards" for url, _ in transport.requests)
    assert any(url == "http://agentgw.local:9001/acn-agent/v1/task-executions" for url, _ in transport.requests)
    assert any(
        url == "http://agentgw.local:9001/acn-agent/v1/task-execution-terminations" for url, _ in transport.requests
    )


def test_agent_deletion_route(test_app: tuple[Any, RecordingTransport]) -> None:
    app, transport = test_app
    asyncio.run(
        post_json(
            app,
            "/idm/v1/identity-applications",
            {"owner": "alice", "name": "AliceAgent", "description": "AgentModel-X, SN123456"},
        )
    )
    response = asyncio.run(post_json(app, "/acn-agent/v1/agent-deletions", {"agent_id": "a-1"}))
    assert response.status_code == 200
    assert response.json()["result"] == "deleted"
    assert any(url == "http://idm.local:9020/acn-agent/v1/agent-deletions" for url, _ in transport.requests)

    owner_response = asyncio.run(post_json(app, "/acn-agent/v1/owner-agents", {"owner": "alice"}))
    assert owner_response.status_code == 200
    assert owner_response.json()["total"] == 1

    delete_saved_response = asyncio.run(post_json(app, "/acn-agent/v1/agent-deletions", {"agent_id": "did:acn:test:1"}))
    assert delete_saved_response.status_code == 200

    owner_response_after_delete = asyncio.run(post_json(app, "/acn-agent/v1/owner-agents", {"owner": "alice"}))
    assert owner_response_after_delete.status_code == 200
    assert owner_response_after_delete.json() == {"owner": "alice", "total": 0, "agents": []}


def test_owner_agents_supports_wrapped_body(test_app: tuple[Any, RecordingTransport]) -> None:
    app, _ = test_app
    asyncio.run(
        post_json(
            app,
            "/idm/v1/identity-applications",
            {
                "body": {
                    "owner": "did:acn:owner:12345",
                    "name": "巡检机器人A",
                    "description": "AgentModel-X, SN123456",
                }
            },
        )
    )

    response = asyncio.run(post_json(app, "/acn-agent/v1/owner-agents", {"body": {"owner": "did:acn:owner:12345"}}))
    assert response.status_code == 200
    assert response.json() == {
        "owner": "did:acn:owner:12345",
        "total": 1,
        "agents": [
            {
                "agent_id": "did:acn:test:1",
                "agent_name": "巡检机器人A",
                "description": "AgentModel-X, SN123456",
            }
        ],
    }


def test_clear_clears_local_state(test_app: tuple[Any, RecordingTransport]) -> None:
    app, _ = test_app
    asyncio.run(
        post_json(
            app,
            "/idm/v1/identity-applications",
            {"owner": "alice", "name": "AliceAgent", "description": "AgentModel-X, SN123456"},
        )
    )
    response = asyncio.run(post_json(app, "/clear", {}))

    assert response.status_code == 200
    assert response.json()["result"] == "success"
    assert response.json()["cleared_records"] >= 1
    assert response.json()["cleared_pipeline_logs"] >= 1

    owner_response = asyncio.run(post_json(app, "/acn-agent/v1/owner-agents", {"owner": "alice"}))
    assert owner_response.status_code == 200
    assert owner_response.json() == {"owner": "alice", "total": 0, "agents": []}


def test_health(test_app: tuple[Any, RecordingTransport]) -> None:
    app, _ = test_app
    asyncio.run(post_json(app, "/idm/v1/identity-applications", {"owner": "alice"}))
    response = asyncio.run(get_json(app, "/health"))

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "ACN Agent"
