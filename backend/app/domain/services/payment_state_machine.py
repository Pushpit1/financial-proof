from app.domain.enums.payment import (
    OrderState,
    PaymentEvent,
    PaymentState,
)
from app.domain.models.payment import Payment, PaymentOrder


class InvalidPaymentTransition(ValueError):
    """Raised when a payment transition is not permitted."""


class InvalidOrderTransition(ValueError):
    """Raised when an order transition is not permitted."""


class PaymentStateMachine:
    """Deterministic domain state machine for payment lifecycle."""

    _TRANSITIONS: dict[
        tuple[PaymentState, PaymentEvent],
        PaymentState,
    ] = {
        (PaymentState.CREATED, PaymentEvent.AUTHORIZE):
            PaymentState.AUTHORIZED,
        (PaymentState.CREATED, PaymentEvent.FAIL):
            PaymentState.FAILED,
        (PaymentState.AUTHORIZED, PaymentEvent.CAPTURE):
            PaymentState.CAPTURED,
        (PaymentState.AUTHORIZED, PaymentEvent.FAIL):
            PaymentState.FAILED,
        (PaymentState.CAPTURED, PaymentEvent.REFUND):
            PaymentState.REFUNDED,
    }

    @classmethod
    def transition(
        cls,
        payment: Payment,
        event: PaymentEvent,
    ) -> Payment:
        """Apply one valid payment transition."""

        key = (payment.state, event)

        try:
            next_state = cls._TRANSITIONS[key]
        except KeyError as exc:
            raise InvalidPaymentTransition(
                f"Cannot apply '{event}' to payment "
                f"in state '{payment.state}'."
            ) from exc

        return Payment(
            order_id=payment.order_id,
            amount_minor=payment.amount_minor,
            currency=payment.currency,
            state=next_state,
            id=payment.id,
            created_at=payment.created_at,
        )


class OrderStateMachine:
    """Deterministic domain state machine for order lifecycle."""

    _TRANSITIONS: dict[
        tuple[OrderState, PaymentEvent],
        OrderState,
    ] = {
        (OrderState.CREATED, PaymentEvent.AUTHORIZE):
            OrderState.AUTHORIZED,
        (OrderState.CREATED, PaymentEvent.FAIL):
            OrderState.FAILED,
        (OrderState.AUTHORIZED, PaymentEvent.CAPTURE):
            OrderState.CAPTURED,
        (OrderState.AUTHORIZED, PaymentEvent.FAIL):
            OrderState.FAILED,
        (OrderState.CREATED, PaymentEvent.CANCEL):
            OrderState.CANCELLED,
    }

    @classmethod
    def transition(
        cls,
        order: PaymentOrder,
        event: PaymentEvent,
    ) -> PaymentOrder:
        """Apply one valid order transition."""

        key = (order.state, event)

        try:
            next_state = cls._TRANSITIONS[key]
        except KeyError as exc:
            raise InvalidOrderTransition(
                f"Cannot apply '{event}' to order "
                f"in state '{order.state}'."
            ) from exc

        return PaymentOrder(
            amount_minor=order.amount_minor,
            currency=order.currency,
            state=next_state,
            id=order.id,
            created_at=order.created_at,
        )
