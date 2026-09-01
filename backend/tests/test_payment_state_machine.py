from uuid import uuid4

import pytest

from app.domain.enums.payment import (
    OrderState,
    PaymentEvent,
    PaymentState,
)
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.services.payment_state_machine import (
    InvalidOrderTransition,
    InvalidPaymentTransition,
    OrderStateMachine,
    PaymentStateMachine,
)


def test_payment_can_authorize() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    result = PaymentStateMachine.transition(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    assert result.state == PaymentState.AUTHORIZED
    assert result.id == payment.id
    assert result.order_id == payment.order_id


def test_payment_can_capture_after_authorization() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
        state=PaymentState.AUTHORIZED,
    )

    result = PaymentStateMachine.transition(
        payment,
        PaymentEvent.CAPTURE,
    )

    assert result.state == PaymentState.CAPTURED


def test_payment_can_refund_after_capture() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
        state=PaymentState.CAPTURED,
    )

    result = PaymentStateMachine.transition(
        payment,
        PaymentEvent.REFUND,
    )

    assert result.state == PaymentState.REFUNDED


def test_invalid_payment_transition_is_rejected() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    with pytest.raises(InvalidPaymentTransition):
        PaymentStateMachine.transition(
            payment,
            PaymentEvent.CAPTURE,
        )


def test_order_can_authorize() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    result = OrderStateMachine.transition(
        order,
        PaymentEvent.AUTHORIZE,
    )

    assert result.state == OrderState.AUTHORIZED
    assert result.id == order.id


def test_order_can_capture_after_authorization() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
        state=OrderState.AUTHORIZED,
    )

    result = OrderStateMachine.transition(
        order,
        PaymentEvent.CAPTURE,
    )

    assert result.state == OrderState.CAPTURED


def test_order_can_cancel_before_authorization() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    result = OrderStateMachine.transition(
        order,
        PaymentEvent.CANCEL,
    )

    assert result.state == OrderState.CANCELLED


def test_invalid_order_transition_is_rejected() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    with pytest.raises(InvalidOrderTransition):
        OrderStateMachine.transition(
            order,
            PaymentEvent.CAPTURE,
        )


def test_payment_transition_is_immutable() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    result = PaymentStateMachine.transition(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    assert payment.state == PaymentState.CREATED
    assert result.state == PaymentState.AUTHORIZED


def test_order_transition_is_immutable() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    result = OrderStateMachine.transition(
        order,
        PaymentEvent.AUTHORIZE,
    )

    assert order.state == OrderState.CREATED
    assert result.state == OrderState.AUTHORIZED
