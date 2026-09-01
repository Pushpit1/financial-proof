from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.enums.payment import OrderState, PaymentState


@dataclass(frozen=True)
class Payment:
    """Immutable representation of a payment aggregate state."""

    order_id: UUID
    amount_minor: int
    currency: str
    state: PaymentState = PaymentState.CREATED
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        if self.amount_minor <= 0:
            raise ValueError("Payment amount must be positive.")

        if len(self.currency) != 3:
            raise ValueError(
                "Payment currency must be a 3-letter code."
            )


@dataclass(frozen=True)
class PaymentOrder:
    """Immutable representation of a payment order."""

    amount_minor: int
    currency: str
    state: OrderState = OrderState.CREATED
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        if self.amount_minor <= 0:
            raise ValueError("Order amount must be positive.")

        if len(self.currency) != 3:
            raise ValueError(
                "Order currency must be a 3-letter code."
            )
