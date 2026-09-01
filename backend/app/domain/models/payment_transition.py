from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.enums.payment import (
    OrderState,
    PaymentEvent,
    PaymentState,
)


@dataclass(frozen=True)
class PaymentTransition:
    """Immutable audit record of one payment state transition."""

    payment_id: UUID
    from_state: PaymentState
    event: PaymentEvent
    to_state: PaymentState
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class OrderTransition:
    """Immutable audit record of one order state transition."""

    order_id: UUID
    from_state: OrderState
    event: PaymentEvent
    to_state: OrderState
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    id: UUID = field(default_factory=uuid4)
