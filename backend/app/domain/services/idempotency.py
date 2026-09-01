from app.domain.models.idempotency import (
    IdempotencyKey,
    IdempotencyRecord,
)


class DuplicateIdempotencyKey(ValueError):
    """Raised when an idempotency key is reused with a new operation."""


class IdempotencyService:
    """Deterministic in-memory idempotency registry for domain operations."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}

    def lookup(
        self,
        key: IdempotencyKey,
    ) -> IdempotencyRecord | None:
        """Return the existing record for a key, if present."""

        return self._records.get(key.value)

    def record(
        self,
        record: IdempotencyRecord,
    ) -> IdempotencyRecord:
        """Record a key exactly once."""

        existing = self._records.get(record.key.value)

        if existing is not None:
            if existing == record:
                return existing

            raise DuplicateIdempotencyKey(
                f"Idempotency key '{record.key.value}' "
                "already belongs to another operation."
            )

        self._records[record.key.value] = record
        return record
