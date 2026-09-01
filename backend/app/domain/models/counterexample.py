from dataclasses import dataclass
from uuid import UUID

from app.domain.models.payment_simulation import PaymentSimulation


@dataclass(frozen=True)
class Counterexample:
    """Immutable failing simulation suitable for deterministic shrinking."""

    simulation_id: UUID
    simulation: PaymentSimulation
    violation_code: str
    original_event_count: int
    minimized_event_count: int

    def __post_init__(self) -> None:
        if self.simulation_id != self.simulation.id:
            raise ValueError(
                "Counterexample simulation_id must match simulation.id."
            )

        if not self.violation_code.strip():
            raise ValueError("Counterexample violation_code cannot be empty.")

        if self.original_event_count < 0:
            raise ValueError(
                "Counterexample original_event_count cannot be negative."
            )

        if self.minimized_event_count < 0:
            raise ValueError(
                "Counterexample minimized_event_count cannot be negative."
            )

        if self.minimized_event_count > self.original_event_count:
            raise ValueError(
                "Counterexample minimized_event_count cannot exceed "
                "original_event_count."
            )

        if self.minimized_event_count != len(self.simulation.events):
            raise ValueError(
                "Counterexample minimized_event_count must match "
                "simulation event count."
            )
