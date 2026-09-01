from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RetryAttack:
    """Description of a deterministic request retry after a lost response."""

    simulation_id: UUID
    target_sequence: int
    retry_count: int

    def __post_init__(self) -> None:
        if self.target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")

        if self.retry_count <= 0:
            raise ValueError("Retry count must be positive.")


@dataclass(frozen=True)
class RetryScenario:
    """Immutable description of a retried payment operation."""

    simulation_id: UUID
    target_sequence: int
    retry_count: int
