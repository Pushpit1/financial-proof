from collections.abc import Iterable

from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_transition import (
    OrderTransition,
    PaymentTransition,
)
from app.domain.services.payment_state_machine import (
    OrderStateMachine,
    PaymentStateMachine,
)


class PaymentTransitionRecorder:
    """Apply payment events while recording immutable transitions."""

    @staticmethod
    def apply(
        payment: Payment,
        event: PaymentEvent,
    ) -> tuple[Payment, PaymentTransition]:
        next_payment = PaymentStateMachine.transition(
            payment,
            event,
        )

        transition = PaymentTransition(
            payment_id=payment.id,
            from_state=payment.state,
            event=event,
            to_state=next_payment.state,
        )

        return next_payment, transition


class OrderTransitionRecorder:
    """Apply order events while recording immutable transitions."""

    @staticmethod
    def apply(
        order: PaymentOrder,
        event: PaymentEvent,
    ) -> tuple[PaymentOrder, OrderTransition]:
        next_order = OrderStateMachine.transition(
            order,
            event,
        )

        transition = OrderTransition(
            order_id=order.id,
            from_state=order.state,
            event=event,
            to_state=next_order.state,
        )

        return next_order, transition


class PaymentTransitionHistory:
    """Immutable ordered payment transition collection."""

    def __init__(
        self,
        transitions: Iterable[PaymentTransition],
    ) -> None:
        self._transitions = tuple(transitions)

    @property
    def transitions(self) -> tuple[PaymentTransition, ...]:
        return self._transitions
