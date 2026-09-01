from uuid import uuid4

import pytest

from app.domain.enums.payment import (
    OrderState,
    PaymentEvent,
    PaymentState,
)
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.services.payment_replay import (
    OrderReplayService,
    PaymentEventHistory,
    PaymentReplayService,
)
from app.domain.services.payment_state_machine import (
    InvalidOrderTransition,
    InvalidPaymentTransition,
)


def test_payment_history_preserves_event_order() -> None:
    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
            PaymentEvent.REFUND,
        )
    )

    assert history.events == (
        PaymentEvent.AUTHORIZE,
        PaymentEvent.CAPTURE,
        PaymentEvent.REFUND,
    )


def test_empty_payment_history_returns_initial_state() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    result = PaymentReplayService.replay(
        payment,
        PaymentEventHistory.from_events(()),
    )

    assert result == payment


def test_payment_replay_reconstructs_final_state() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
            PaymentEvent.REFUND,
        )
    )

    result = PaymentReplayService.replay(payment, history)

    assert result.state == PaymentState.REFUNDED
    assert result.id == payment.id
    assert result.order_id == payment.order_id
    assert result.amount_minor == payment.amount_minor
    assert result.currency == payment.currency


def test_payment_replay_does_not_mutate_initial_state() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
        )
    )

    result = PaymentReplayService.replay(payment, history)

    assert payment.state == PaymentState.CREATED
    assert result.state == PaymentState.CAPTURED


def test_payment_replay_is_deterministic() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=2500,
        currency="INR",
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
        )
    )

    first = PaymentReplayService.replay(payment, history)
    second = PaymentReplayService.replay(payment, history)

    assert first == second


def test_payment_replay_rejects_invalid_sequence() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.CAPTURE,
        )
    )

    with pytest.raises(InvalidPaymentTransition):
        PaymentReplayService.replay(payment, history)


def test_payment_replay_rejects_duplicate_capture() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
        state=PaymentState.AUTHORIZED,
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.CAPTURE,
            PaymentEvent.CAPTURE,
        )
    )

    with pytest.raises(InvalidPaymentTransition):
        PaymentReplayService.replay(payment, history)


def test_payment_replay_rejects_duplicate_refund() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
        state=PaymentState.CAPTURED,
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.REFUND,
            PaymentEvent.REFUND,
        )
    )

    with pytest.raises(InvalidPaymentTransition):
        PaymentReplayService.replay(payment, history)


def test_order_replay_reconstructs_final_state() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
        )
    )

    result = OrderReplayService.replay(order, history)

    assert result.state == OrderState.CAPTURED
    assert result.id == order.id
    assert result.amount_minor == order.amount_minor
    assert result.currency == order.currency


def test_order_replay_supports_cancellation() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.CANCEL,
        )
    )

    result = OrderReplayService.replay(order, history)

    assert result.state == OrderState.CANCELLED


def test_order_replay_does_not_mutate_initial_state() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
        )
    )

    result = OrderReplayService.replay(order, history)

    assert order.state == OrderState.CREATED
    assert result.state == OrderState.CAPTURED


def test_order_replay_is_deterministic() -> None:
    order = PaymentOrder(
        amount_minor=5000,
        currency="INR",
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
        )
    )

    first = OrderReplayService.replay(order, history)
    second = OrderReplayService.replay(order, history)

    assert first == second


def test_order_replay_rejects_invalid_sequence() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.CAPTURE,
        )
    )

    with pytest.raises(InvalidOrderTransition):
        OrderReplayService.replay(order, history)


def test_order_replay_rejects_duplicate_authorization() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.AUTHORIZE,
        )
    )

    with pytest.raises(InvalidOrderTransition):
        OrderReplayService.replay(order, history)


def test_history_is_immutable() -> None:
    history = PaymentEventHistory.from_events(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
        )
    )

    with pytest.raises(AttributeError):
        history.events += (PaymentEvent.REFUND,)
