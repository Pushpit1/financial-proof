from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.services.payment_state_machine import (
    OrderStateMachine,
    PaymentStateMachine,
)


@dataclass(frozen=True)
class PaymentEventHistory:
    """Immutable ordered history of payment lifecycle events."""

    events: tuple[PaymentEvent, ...]

    @classmethod
    def from_events(
        cls,
        events: Iterable[PaymentEvent],
    ) -> "PaymentEventHistory":
        return cls(events=tuple(events))


class PaymentReplayService:
    """Deterministically reconstruct payment state from ordered events."""

    @staticmethod
    def replay(
        initial_state: Payment,
        history: PaymentEventHistory,
    ) -> Payment:
        """Replay payment events in their exact recorded order."""

        current = initial_state

        for event in history.events:
            current = PaymentStateMachine.transition(current, event)

        return current


class OrderReplayService:
    """Deterministically reconstruct order state from ordered events."""

    @staticmethod
    def replay(
        initial_state: PaymentOrder,
        history: PaymentEventHistory,
    ) -> PaymentOrder:
        """Replay order events in their exact recorded order."""

        current = initial_state

        for event in history.events:
            current = OrderStateMachine.transition(current, event)

        return current
