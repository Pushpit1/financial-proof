from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LostResponseAttack:
    """Description of a deterministic lost-response failure."""

    simulation_id: UUID
    target_sequence: int

    def __post_init__(self) -> None:
        if self.target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")


@dataclass(frozen=True)
class LostResponseScenario:
    """Immutable description of an execution where a response is lost."""

    simulation_id: UUID
    target_sequence: int
    response_lost: bool = True
