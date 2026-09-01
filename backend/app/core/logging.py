import logging
import sys
from collections.abc import Mapping
from typing import Any

import structlog


def configure_logging() -> None:
    """Configure structured application logging."""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return the canonical structured logger."""

    return structlog.get_logger(name)


def log_event(
    logger: structlog.stdlib.BoundLogger,
    event: str,
    *,
    fields: Mapping[str, Any] | None = None,
) -> None:
    """Emit a structured application event."""

    event_fields = dict(fields or {})
    logger.info(event, **event_fields)
