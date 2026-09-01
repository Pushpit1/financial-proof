import threading

from app.domain.models.idempotency import IdempotencyKey
from app.domain.services.idempotency import IdempotencyService
from app.domain.services.idempotent_execution import IdempotentExecutionService


def test_concurrent_same_key_has_single_execution() -> None:
    service = IdempotentExecutionService(IdempotencyService())
    key = IdempotencyKey("capture-race")

    results = []
    errors = []

    def worker() -> None:
        try:
            results.append(
                service.execute(
                    key,
                    "capture-response",
                )
            )
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=worker),
        threading.Thread(target=worker),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert not errors
    assert len(results) == 2
    assert sum(result.executed for result in results) == 1
    assert sum(not result.executed for result in results) == 1


def test_concurrent_different_keys_execute_independently() -> None:
    service = IdempotentExecutionService(IdempotencyService())

    results = []

    def worker(key: str) -> None:
        results.append(
            service.execute(
                IdempotencyKey(key),
                f"{key}-response",
            )
        )

    import threading

    threads = [
        threading.Thread(target=worker, args=("capture-a",)),
        threading.Thread(target=worker, args=("capture-b",)),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(results) == 2
    assert all(result.executed for result in results)
    assert {result.response_fingerprint for result in results} == {
        "capture-a-response",
        "capture-b-response",
    }
