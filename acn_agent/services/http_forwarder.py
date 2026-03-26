from __future__ import annotations

import logging
from typing import Any

import httpx


class HTTPForwarder:
    """HTTP forwarding wrapper around httpx."""

    def __init__(self, timeout_seconds: float, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._timeout = timeout_seconds
        self._transport = transport
        self._logger = logging.getLogger(self.__class__.__name__)

    async def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """POST JSON payload to an upstream service."""
        self._logger.info("开始转发请求到上游 url=%s body=%s", url, payload)
        async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport, trust_env=False) as client:
            response = await client.post(url, json=payload, headers=headers)
        self._logger.info(
            "上游响应完成 url=%s status=%s body=%s",
            url,
            response.status_code,
            response.text,
        )
        return response
