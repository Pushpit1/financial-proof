from dataclasses import dataclass
from datetime import datetime

from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder


@dataclass(frozen=True)
class SimulationSnapshot:
    """Immutable state snapshot captured during simulation execution."""

    sequence: int
    event: PaymentEvent | None
    occurred_at: datetime
    payment: Payment
    order: PaymentOrder

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("Snapshot sequence cannot be negative.")
