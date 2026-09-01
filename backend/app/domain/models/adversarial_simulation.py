from dataclasses import dataclass
from uuid import UUID

from app.domain.models.payment_simulation import PaymentSimulation


@dataclass(frozen=True)
class AdversarialAttack:
    """Base description of a deterministic adversarial transformation."""

    simulation_id: UUID


@dataclass(frozen=True)
class DuplicateEventAttack(AdversarialAttack):
    """Description of a duplicate event injection."""

    target_sequence: int

    def __post_init__(self) -> None:
        if self.target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")


@dataclass(frozen=True)
class OutOfOrderEventAttack(AdversarialAttack):
    """Description of an out-of-order event delivery."""

    source_sequence: int
    target_sequence: int

    def __post_init__(self) -> None:
        if self.source_sequence < 0 or self.target_sequence < 0:
            raise ValueError("Event sequences cannot be negative.")

        if self.source_sequence == self.target_sequence:
            raise ValueError(
                "Source and target sequences must be different."
            )


@dataclass(frozen=True)
class DelayedEventAttack(AdversarialAttack):
    """Description of delayed event delivery."""

    target_sequence: int
    delivery_delay_seconds: int

    def __post_init__(self) -> None:
        if self.target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")

        if self.delivery_delay_seconds <= 0:
            raise ValueError("Delivery delay must be positive.")


@dataclass(frozen=True)
class AdversarialSimulation:
    """Immutable simulation produced by an adversarial transformation."""

    source_simulation: PaymentSimulation
    attack: AdversarialAttack
    simulation: PaymentSimulation
