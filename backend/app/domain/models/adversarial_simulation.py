from dataclasses import dataclass
from uuid import UUID

from app.domain.models.payment_simulation import PaymentSimulation


@dataclass(frozen=True)
class DuplicateEventAttack:
    """Immutable description of one duplicate simulation-event injection."""

    simulation_id: UUID
    target_sequence: int

    def __post_init__(self) -> None:
        if self.target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")


@dataclass(frozen=True)
class AdversarialSimulation:
    """Immutable simulation produced by an adversarial transformation."""

    source_simulation: PaymentSimulation
    attack: DuplicateEventAttack
    simulation: PaymentSimulation
