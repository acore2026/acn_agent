from __future__ import annotations

import logging
from logging.config import dictConfig


def configure_logging(log_level: str) -> None:
    """Configure application logging."""
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                }
            },
            "root": {"level": log_level.upper(), "handlers": ["default"]},
        }
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
