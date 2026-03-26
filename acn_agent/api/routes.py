from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from acn_agent.models.common import ClearResponse
from acn_agent.services.agent_service import AgentService

router = APIRouter()


async def get_agent_service(request: Request) -> AgentService:
    """Return application-scoped agent service."""
    return request.app.state.agent_service  # type: ignore[no-any-return]


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": request.app.title,
        "metrics": request.app.state.metrics.snapshot(),
    }


@router.post("/clear", response_model=ClearResponse)
async def clear_state(agent_service: AgentService = Depends(get_agent_service)) -> ClearResponse:
    """Handle WebUI clear request."""
    return agent_service.clear_state()


@router.post("/idm/v1/identity-applications")
async def identity_applications(
    request: Request,
    agent_service: AgentService = Depends(get_agent_service),
) -> JSONResponse:
    """Proxy identity application requests to IDM."""
    return await _proxy(request, agent_service)


@router.post("/arf/v1/agent-cards")
async def agent_cards(
    request: Request,
    agent_service: AgentService = Depends(get_agent_service),
) -> JSONResponse:
    """Proxy agent card requests to AgentGW."""
    return await _proxy(request, agent_service)


@router.post("/acn-agent/v1/task-executions")
async def task_executions(
    request: Request,
    agent_service: AgentService = Depends(get_agent_service),
) -> JSONResponse:
    """Proxy task execution requests to AgentGW."""
    return await _proxy(request, agent_service)


@router.post("/acn-agent/v1/agent-deletions")
async def agent_deletions(
    request: Request,
    agent_service: AgentService = Depends(get_agent_service),
) -> JSONResponse:
    """Proxy agent deletion requests to IDM."""
    return await _proxy(request, agent_service)


@router.post("/acn-agent/v1/task-execution-terminations")
async def task_execution_terminations(
    request: Request,
    agent_service: AgentService = Depends(get_agent_service),
) -> JSONResponse:
    """Proxy task termination requests to AgentGW."""
    return await _proxy(request, agent_service)


async def _proxy(request: Request, agent_service: AgentService) -> JSONResponse:
    """Shared proxy handler."""
    payload = await request.json()
    headers = {
        "Content-Type": request.headers.get("content-type", "application/json"),
    }
    try:
        status_code, response_body = await agent_service.proxy_request(
            path=request.url.path,
            payload=payload,
            headers=headers,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"上游服务调用失败: {exc}",
        ) from exc
    return JSONResponse(status_code=status_code, content=response_body)
