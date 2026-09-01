from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PartialFailureAttack:
    """Description of an operation that fails after execution begins."""

    simulation_id: UUID
    target_sequence: int

    def __post_init__(self) -> None:
        if self.target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")


@dataclass(frozen=True)
class PartialFailureScenario:
    """Immutable description of an operation interrupted mid-flight."""

    simulation_id: UUID
    target_sequence: int
    operation_started: bool = True
    operation_completed: bool = False
