from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application runtime settings."""

    app_name: str = "ACN Agent"
    app_host: str = "0.0.0.0"
    app_port: int = 9010
    idm_host: str = "127.0.0.1"
    idm_port: int = 9020
    agent_gw_host: str = "127.0.0.1"
    agent_gw_port: int = 9001
    webui_scheme: str = "https"
    webui_host: str = "127.0.0.1"
    webui_port: int = 9005
    webui_verify_ssl: bool = False
    request_timeout_seconds: float = 10.0
    log_level: str = "INFO"
    enable_pipeline_log_push: bool = True
    agent_db_path: str = str(Path(__file__).resolve().parents[2] / "acn_agent.db")

    def base_url(self, host: str, port: int) -> str:
        """Build a backend base URL."""
        return f"http://{host}:{port}"

    def webui_base_url(self) -> str:
        """Build the WebUI base URL."""
        return f"{self.webui_scheme}://{self.webui_host}:{self.webui_port}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()
