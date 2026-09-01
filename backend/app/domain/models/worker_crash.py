from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class WorkerCrashAttack:
    """Description of a deterministic worker crash."""

    simulation_id: UUID
    target_sequence: int

    def __post_init__(self) -> None:
        if self.target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")


@dataclass(frozen=True)
class WorkerCrashScenario:
    """Immutable description of a worker crash and restart."""

    simulation_id: UUID
    target_sequence: int
    restarted: bool = True
