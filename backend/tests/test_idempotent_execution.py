from app.domain.models.idempotency import IdempotencyKey
from app.domain.services.idempotency import IdempotencyService
from app.domain.services.idempotent_execution import IdempotentExecutionService


def test_first_request_executes() -> None:
    service = IdempotentExecutionService(IdempotencyService())

    result = service.execute(
        IdempotencyKey("capture-123"),
        "capture-response",
    )

    assert result.executed is True
    assert result.response_fingerprint == "capture-response"


def test_retry_replays_without_second_execution() -> None:
    service = IdempotentExecutionService(IdempotencyService())
    key = IdempotencyKey("capture-123")

    first = service.execute(key, "capture-response")
    second = service.execute(key, "capture-response")

    assert first.executed is True
    assert second.executed is False
    assert second.response_fingerprint == first.response_fingerprint


def test_retry_returns_same_response_fingerprint() -> None:
    service = IdempotentExecutionService(IdempotencyService())
    key = IdempotencyKey("capture-123")

    service.execute(key, "capture-response")
    retry = service.execute(key, "capture-response")

    assert retry.response_fingerprint == "capture-response"


def test_conflicting_retry_is_rejected() -> None:
    service = IdempotentExecutionService(IdempotencyService())
    key = IdempotencyKey("capture-123")

    service.execute(key, "capture-response")

    try:
        service.execute(key, "different-response")
    except ValueError as exc:
        assert "different response" in str(exc)
    else:
        raise AssertionError("Expected conflicting retry to be rejected.")


def test_different_keys_execute_independently() -> None:
    service = IdempotentExecutionService(IdempotencyService())

    first = service.execute(
        IdempotencyKey("capture-123"),
        "capture-response",
    )
    second = service.execute(
        IdempotencyKey("capture-456"),
        "capture-response",
    )

    assert first.executed is True
    assert second.executed is True
