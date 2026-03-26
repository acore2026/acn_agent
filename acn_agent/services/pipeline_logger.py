from __future__ import annotations

import logging
from typing import Any

import httpx

from acn_agent.core.config import Settings
from acn_agent.models.common import PipelineLog
from acn_agent.services.http_forwarder import HTTPForwarder
from acn_agent.services.state_store import StateStore


class PipelineLogger:
    """Persist and optionally push pipeline logs to WebUI."""

    def __init__(
        self,
        settings: Settings,
        store: StateStore,
        forwarder: HTTPForwarder,
    ) -> None:
        self._settings = settings
        self._store = store
        self._forwarder = forwarder
        self._logger = logging.getLogger(self.__class__.__name__)

    async def emit(
        self,
        source: str,
        destination: str,
        content: Any,
        abstract: str,
        task_id: str | None = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        """Create and push one pipeline log entry."""
        log_item = PipelineLog(
            source=source,
            destination=destination,
            task_id=task_id,
            headers=headers or {},
            abstract=abstract,
            content=content,
        )
        self._store.add_pipeline_log(log_item)
        self._logger.info("记录流水日志 source=%s destination=%s content=%s", source, destination, content)
        if not self._settings.enable_pipeline_log_push:
            return

        webui_url = (
            f"{self._settings.base_url(self._settings.webui_host, self._settings.webui_port)}"
            "/acn/v3/pipeline-logs"
        )
        try:
            await self._forwarder.post_json(webui_url, log_item.model_dump(mode="json"))
        except httpx.HTTPError as exc:
            self._logger.warning("推送流水日志到WebUI失败 error=%s", exc)
