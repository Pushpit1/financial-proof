from threading import Lock

from app.domain.models.idempotency import IdempotencyKey, IdempotencyRecord
from app.domain.models.idempotent_execution import IdempotentExecutionResult
from app.domain.services.idempotency import IdempotencyService


class IdempotentExecutionService:
    """Execute a logical operation exactly once under concurrent retries."""

    def __init__(self, idempotency: IdempotencyService) -> None:
        self._idempotency = idempotency
        self._lock = Lock()

    def execute(
        self,
        key: IdempotencyKey,
        response_fingerprint: str,
    ) -> IdempotentExecutionResult:
        with self._lock:
            existing = self._idempotency.lookup(key)

            if existing is not None:
                if existing.response_fingerprint != response_fingerprint:
                    raise ValueError(
                        "Idempotency key was reused with a different response."
                    )

                return IdempotentExecutionResult(
                    response_fingerprint=existing.response_fingerprint,
                    executed=False,
                )

            record = IdempotencyRecord(
                key=key,
                response_fingerprint=response_fingerprint,
            )

            stored = self._idempotency.record(record)

            return IdempotentExecutionResult(
                response_fingerprint=stored.response_fingerprint,
                executed=True,
            )
