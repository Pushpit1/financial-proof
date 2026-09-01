import json

import structlog

from app.core.logging import configure_logging, get_logger, log_event


def test_configure_logging_sets_structlog_processors() -> None:
    configure_logging()

    logger = get_logger("test")

    assert logger is not None


def test_get_logger_returns_structured_logger() -> None:
    logger = get_logger("financial-proof")

    assert logger is not None
    assert callable(logger.info)


def test_log_event_emits_structured_event(
    capsys,
) -> None:
    configure_logging()

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        correlation_id="corr-123",
    )

    logger = get_logger("test")

    log_event(
        logger,
        "verification.completed",
        fields={
            "verification_id": "verification-123",
            "status": "passed",
        },
    )

    output = capsys.readouterr().out.strip()
    payload = json.loads(output)

    assert payload["event"] == "verification.completed"
    assert payload["verification_id"] == "verification-123"
    assert payload["status"] == "passed"
    assert payload["correlation_id"] == "corr-123"
    assert payload["level"] == "info"
    assert "timestamp" in payload
