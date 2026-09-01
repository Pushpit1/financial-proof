from dataclasses import dataclass


@dataclass(frozen=True)
class IdempotentExecutionResult:
    """Result of executing or replaying an idempotent request."""

    response_fingerprint: str
    executed: bool
