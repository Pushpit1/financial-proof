from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class StaleWorkerStateAttack:
    """Description of a worker attempting to apply stale state."""

    simulation_id: UUID
    worker_sequence: int
    incoming_sequence: int

    def __post_init__(self) -> None:
        if self.worker_sequence < 0:
            raise ValueError("Worker sequence cannot be negative.")

        if self.incoming_sequence < 0:
            raise ValueError("Incoming sequence cannot be negative.")
