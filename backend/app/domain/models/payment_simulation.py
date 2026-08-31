from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder


@dataclass(frozen=True)
class SimulationEvent:
    """One deterministic event executed during a payment simulation."""

    sequence: int
    event: PaymentEvent
    occurred_at: datetime
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("Simulation event sequence cannot be negative.")


@dataclass(frozen=True)
class SimulationTraceEntry:
    """Immutable record of one simulation execution step."""

    sequence: int
    event: PaymentEvent
    occurred_at: datetime
    payment_before: Payment
    payment_after: Payment
    order_before: PaymentOrder
    order_after: PaymentOrder


@dataclass(frozen=True)
class SimulationStateSnapshot:
    """Immutable state captured after a simulation event."""

    sequence: int
    occurred_at: datetime
    payment: Payment
    order: PaymentOrder

    def __iter__(self):
        """Allow snapshot unpacking as (payment, order)."""

        yield self.payment
        yield self.order

    def __eq__(self, other) -> bool:
        """Support both snapshot-to-snapshot and state-tuple comparison."""

        if isinstance(other, SimulationStateSnapshot):
            return (
                self.sequence == other.sequence
                and self.occurred_at == other.occurred_at
                and self.payment == other.payment
                and self.order == other.order
            )

        if isinstance(other, tuple) and len(other) == 2:
            return self.payment == other[0] and self.order == other[1]

        return NotImplemented


@dataclass(frozen=True)
class PaymentSimulation:
    """Immutable definition of a deterministic payment simulation."""

    seed: int
    initial_payment: Payment
    initial_order: PaymentOrder
    events: tuple[SimulationEvent, ...] = ()
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        sequences = tuple(event.sequence for event in self.events)

        if sequences != tuple(range(len(sequences))):
            raise ValueError(
                "Simulation event sequences must be contiguous and ordered."
            )


@dataclass(frozen=True)
class SimulationResult:
    """Immutable result produced by a simulation run."""

    simulation_id: UUID
    seed: int
    initial_payment: Payment
    initial_order: PaymentOrder
    final_payment: Payment
    final_order: PaymentOrder
    trace: tuple[SimulationTraceEntry, ...]
    snapshots: tuple[SimulationStateSnapshot, ...] = ()
