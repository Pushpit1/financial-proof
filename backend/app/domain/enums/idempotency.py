from enum import StrEnum


class IdempotencyStatus(StrEnum):
    """Runtime status of an idempotency key."""

    NEW = "new"
    PROCESSING = "processing"
    COMPLETED = "completed"
