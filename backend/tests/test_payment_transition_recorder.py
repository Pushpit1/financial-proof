from uuid import uuid4

from app.domain.enums.payment import (
    OrderState,
    PaymentEvent,
    PaymentState,
)
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.services.payment_transition_recorder import (
    OrderTransitionRecorder,
    PaymentTransitionHistory,
    PaymentTransitionRecorder,
)


def test_payment_transition_records_state_change() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    result, transition = PaymentTransitionRecorder.apply(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    assert result.state == PaymentState.AUTHORIZED
    assert transition.payment_id == payment.id
    assert transition.from_state == PaymentState.CREATED
    assert transition.event == PaymentEvent.AUTHORIZE
    assert transition.to_state == PaymentState.AUTHORIZED


def test_order_transition_records_state_change() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    result, transition = OrderTransitionRecorder.apply(
        order,
        PaymentEvent.AUTHORIZE,
    )

    assert result.state == OrderState.AUTHORIZED
    assert transition.order_id == order.id
    assert transition.from_state == OrderState.CREATED
    assert transition.event == PaymentEvent.AUTHORIZE
    assert transition.to_state == OrderState.AUTHORIZED


def test_payment_transition_history_preserves_order() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    authorized, first = PaymentTransitionRecorder.apply(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    _, second = PaymentTransitionRecorder.apply(
        authorized,
        PaymentEvent.CAPTURE,
    )

    history = PaymentTransitionHistory(
        (first, second),
    )

    assert history.transitions == (first, second)


def test_transition_history_is_immutable() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    _, transition = PaymentTransitionRecorder.apply(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    history = PaymentTransitionHistory((transition,))

    assert isinstance(history.transitions, tuple)


def test_transition_records_are_immutable() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    _, transition = PaymentTransitionRecorder.apply(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    import dataclasses

    assert dataclasses.is_dataclass(transition)

    import pytest

    with pytest.raises(dataclasses.FrozenInstanceError):
        transition.to_state = PaymentState.FAILED


def test_transition_identity_is_preserved() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    _, transition = PaymentTransitionRecorder.apply(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    assert transition.payment_id == payment.id
    assert transition.id is not None


def test_transition_has_timestamp() -> None:
    payment = Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )

    _, transition = PaymentTransitionRecorder.apply(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    assert transition.occurred_at.tzinfo is not None
