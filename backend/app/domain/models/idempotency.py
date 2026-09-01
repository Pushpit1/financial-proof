from dataclasses import dataclass


@dataclass(frozen=True)
class IdempotencyKey:
    """Immutable idempotency key used to identify a logical request."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Idempotency key cannot be empty.")


@dataclass(frozen=True)
class IdempotencyRecord:
    """Immutable record of a completed idempotent operation."""

    key: IdempotencyKey
    response_fingerprint: str

    def __post_init__(self) -> None:
        if not self.response_fingerprint.strip():
            raise ValueError(
                "Response fingerprint cannot be empty."
            )
