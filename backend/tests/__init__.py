from app.domain.models.idempotency import IdempotencyKey
from app.domain.services.idempotency import IdempotencyService
from app.domain.services.idempotent_execution import IdempotentExecutionService


def test_worker_restart_retry_executes_operation_once() -> None:
    idempotency = IdempotencyService()

    first_worker = IdempotentExecutionService(idempotency)
    restarted_worker = IdempotentExecutionService(idempotency)

    key = IdempotencyKey("capture-worker-restart")

    first = first_worker.execute(
        key,
        "capture-response",
    )

    retry = restarted_worker.execute(
        key,
        "capture-response",
    )

    assert first.executed is True
    assert retry.executed is False
    assert retry.response_fingerprint == first.response_fingerprint


def test_worker_restart_preserves_conflicting_key_protection() -> None:
    idempotency = IdempotencyService()

    first_worker = IdempotentExecutionService(idempotency)
    restarted_worker = IdempotentExecutionService(idempotency)

    key = IdempotencyKey("capture-worker-restart-conflict")

    first_worker.execute(
        key,
        "capture-response",
    )

    try:
        restarted_worker.execute(
            key,
            "different-response",
        )
    except ValueError as exc:
        assert "different response" in str(exc)
    else:
        raise AssertionError("Expected conflicting retry to be rejected.")


def test_multiple_restarts_still_replay_same_result() -> None:
    idempotency = IdempotencyService()
    key = IdempotencyKey("capture-multiple-restarts")

    first = IdempotentExecutionService(idempotency)
    second = IdempotentExecutionService(idempotency)
    third = IdempotentExecutionService(idempotency)

    first_result = first.execute(key, "capture-response")
    second_result = second.execute(key, "capture-response")
    third_result = third.execute(key, "capture-response")

    assert first_result.executed is True
    assert second_result.executed is False
    assert third_result.executed is False

    assert second_result.response_fingerprint == "capture-response"
    assert third_result.response_fingerprint == "capture-response"

