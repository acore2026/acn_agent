from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import Any

import httpx

from acn_agent.core.config import Settings
from acn_agent.models.common import ClearResponse, OwnerAgent, OwnerAgentsResponse, ProxyRecord
from acn_agent.services.http_forwarder import HTTPForwarder
from acn_agent.services.agent_repository import AgentRepository
from acn_agent.services.pipeline_logger import PipelineLogger
from acn_agent.services.state_store import StateStore


@dataclass(frozen=True)
class RouteTarget:
    """Route mapping to one upstream service."""

    upstream_name: str
    upstream_url: str


class AgentService:
    """ACN Agent business orchestration."""

    def __init__(
        self,
        settings: Settings,
        store: StateStore,
        agent_repository: AgentRepository,
        forwarder: HTTPForwarder,
        pipeline_logger: PipelineLogger,
    ) -> None:
        self._settings = settings
        self._store = store
        self._agent_repository = agent_repository
        self._forwarder = forwarder
        self._pipeline_logger = pipeline_logger
        self._logger = logging.getLogger(self.__class__.__name__)

    def resolve_target(self, path: str) -> RouteTarget:
        """Map request path to upstream service."""
        if path in {"/idm/v1/identity-applications", "/acn-agent/v1/agent-deletions"}:
            return RouteTarget(
                upstream_name="IDM",
                upstream_url=f"{self._settings.base_url(self._settings.idm_host, self._settings.idm_port)}{path}",
            )
        if path in {
            "/arf/v1/agent-cards",
            "/acn-agent/v1/task-executions",
            "/acn-agent/v1/task-execution-terminations",
        }:
            return RouteTarget(
                upstream_name="AgentGW",
                upstream_url=f"{self._settings.base_url(self._settings.agent_gw_host, self._settings.agent_gw_port)}{path}",
            )
        raise ValueError(f"Unsupported path: {path}")

    async def proxy_request(
        self,
        path: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> tuple[int, Any]:
        """Forward one ACN SDK request to the mapped upstream."""
        target = self.resolve_target(path)
        self._logger.info("接收到ACN SDK请求 path=%s upstream=%s body=%s", path, target.upstream_name, payload)
        await self._pipeline_logger.emit(
            source="ACN SDK",
            destination="ACN Agent",
            content=payload,
            abstract=f"收到{path}请求",
            task_id=self._extract_task_id(payload),
            headers=headers,
        )

        try:
            response = await self._forwarder.post_json(target.upstream_url, payload, headers=headers)
            response_body = self._parse_response(response)
        except httpx.HTTPError as exc:
            self._logger.exception("上游转发失败 path=%s error=%s", path, exc)
            await self._pipeline_logger.emit(
                source="ACN Agent",
                destination=target.upstream_name,
                content={"error": str(exc)},
                abstract=f"{path}转发失败",
                task_id=self._extract_task_id(payload),
            )
            raise

        self._store.add_record(
            ProxyRecord(
                path=path,
                upstream_name=target.upstream_name,
                upstream_url=target.upstream_url,
                request_body=payload,
                response_status=response.status_code,
                response_body=response_body,
            )
        )
        await self._pipeline_logger.emit(
            source="ACN Agent",
            destination=target.upstream_name,
            content=payload,
            abstract=f"{path}已转发到{target.upstream_name}",
            task_id=self._extract_task_id(payload),
            headers=headers,
        )
        await self._pipeline_logger.emit(
            source=target.upstream_name,
            destination="ACN Agent",
            content=response_body,
            abstract=f"{path}上游响应返回",
            task_id=self._extract_task_id(payload),
        )
        await self._pipeline_logger.emit(
            source="ACN Agent",
            destination="ACN SDK",
            content=response_body,
            abstract=f"{path}响应返回ACN SDK",
            task_id=self._extract_task_id(payload),
        )
        self._sync_local_agent_state(path=path, payload=payload, response_status=response.status_code, response_body=response_body)
        return response.status_code, response_body

    def clear_state(self) -> ClearResponse:
        """Clear local runtime state."""
        self._logger.info("收到WebUI清除请求，开始清理本地状态")
        records_count, log_count = self._store.clear()
        deleted_agents = self._agent_repository.clear()
        self._logger.info("本地状态已清理 cleared_records=%s cleared_pipeline_logs=%s", records_count, log_count)
        self._logger.info("本地Agent表已清理 cleared_agents=%s", deleted_agents)
        return ClearResponse(
            message="本地状态清理完成",
            cleared_records=records_count,
            cleared_pipeline_logs=log_count,
        )

    def get_owner_agents(self, payload: dict[str, Any]) -> OwnerAgentsResponse:
        """Return locally persisted agents for the requested owner."""
        body = self._get_request_body(payload)
        owner = body.get("owner")
        if not owner:
            raise ValueError("owner is required")

        agents = self._agent_repository.list_agents_by_owner(str(owner))
        return OwnerAgentsResponse(
            owner=str(owner),
            total=len(agents),
            agents=[
                OwnerAgent(
                    agent_id=agent.agent_id,
                    agent_name=agent.agent_name,
                    description=agent.description,
                )
                for agent in agents
            ],
        )

    @staticmethod
    def _parse_response(response: httpx.Response) -> Any:
        """Parse upstream response body."""
        if not response.text:
            return {}
        try:
            return response.json()
        except ValueError:
            return {"raw_text": response.text}

    @staticmethod
    def _extract_task_id(payload: dict[str, Any]) -> str | None:
        """Extract task_id if present."""
        task_id = payload.get("task_id")
        return str(task_id) if task_id is not None else None

    @staticmethod
    def _get_request_body(payload: dict[str, Any]) -> dict[str, Any]:
        """Support wrapped and flat request payloads."""
        body = payload.get("body")
        return body if isinstance(body, dict) else payload

    def _sync_local_agent_state(self, path: str, payload: dict[str, Any], response_status: int, response_body: Any) -> None:
        """Persist or delete local Agent rows after successful upstream processing."""
        if response_status < 200 or response_status >= 300:
            return

        body = self._get_request_body(payload)
        try:
            if path == "/idm/v1/identity-applications":
                owner = body.get("owner")
                agent_name = body.get("name") or body.get("agent_name")
                description = body.get("description", "")
                agent_id = response_body.get("agent_id") if isinstance(response_body, dict) else None
                if owner and agent_name and agent_id:
                    self._agent_repository.upsert_agent(
                        owner=str(owner),
                        agent_id=str(agent_id),
                        agent_name=str(agent_name),
                        description=str(description),
                    )
                    self._logger.info("本地Agent信息已保存 agent_id=%s owner=%s", agent_id, owner)
            elif path == "/acn-agent/v1/agent-deletions":
                agent_id = body.get("agent_id")
                if agent_id:
                    self._agent_repository.delete_agent(str(agent_id))
                    self._logger.info("本地Agent信息已删除 agent_id=%s", agent_id)
        except sqlite3.Error as exc:
            self._logger.exception("本地Agent表操作失败 path=%s error=%s", path, exc)
            raise RuntimeError(f"本地Agent信息保存失败: {exc}") from exc
