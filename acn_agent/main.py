from __future__ import annotations

from fastapi import FastAPI

from acn_agent.api.routes import router
from acn_agent.core.config import Settings, get_settings
from acn_agent.core.logging import configure_logging
from acn_agent.services.agent_service import AgentService
from acn_agent.services.http_forwarder import HTTPForwarder
from acn_agent.services.metrics import MetricsRegistry
from acn_agent.services.pipeline_logger import PipelineLogger
from acn_agent.services.state_store import StateStore


def create_app(
    settings: Settings | None = None,
    transport=None,
) -> FastAPI:
    """Application factory."""
    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)
    store = StateStore()
    metrics = MetricsRegistry()
    forwarder = HTTPForwarder(
        timeout_seconds=runtime_settings.request_timeout_seconds,
        transport=transport,
    )
    pipeline_logger = PipelineLogger(runtime_settings, store, forwarder)

    app = FastAPI(
        title=runtime_settings.app_name,
        version="1.0.0",
    )
    app.state.metrics = metrics
    app.state.agent_service = AgentService(
        settings=runtime_settings,
        store=store,
        metrics=metrics,
        forwarder=forwarder,
        pipeline_logger=pipeline_logger,
    )
    app.include_router(router)
    return app


app = create_app()
