from dataclasses import FrozenInstanceError

import pytest

from app.domain.enums.payment import OrderState, PaymentEvent, PaymentState
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
    SimulationStateSnapshot,
    SimulationTraceEntry,
)


def make_payment() -> Payment:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )
    return Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
    )


def make_order() -> PaymentOrder:
    return PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )


def test_payment_rejects_non_positive_amount() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    with pytest.raises(
        ValueError,
        match="Payment amount must be positive",
    ):
        Payment(
            order_id=order.id,
            amount_minor=0,
            currency="INR",
        )


def test_order_rejects_non_positive_amount() -> None:
    with pytest.raises(
        ValueError,
        match="Order amount must be positive",
    ):
        PaymentOrder(
            amount_minor=0,
            currency="INR",
        )


def test_payment_rejects_invalid_currency_length() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )

    with pytest.raises(
        ValueError,
        match="Payment currency must be a 3-letter code",
    ):
        Payment(
            order_id=order.id,
            amount_minor=1000,
            currency="US",
        )


def test_order_rejects_invalid_currency_length() -> None:
    with pytest.raises(
        ValueError,
        match="Order currency must be a 3-letter code",
    ):
        PaymentOrder(
            amount_minor=1000,
            currency="US",
        )


def test_payment_is_immutable() -> None:
    payment = make_payment()

    with pytest.raises(FrozenInstanceError):
        payment.state = PaymentState.AUTHORIZED


def test_order_is_immutable() -> None:
    order = make_order()

    with pytest.raises(FrozenInstanceError):
        order.state = OrderState.AUTHORIZED


def test_simulation_event_rejects_negative_sequence() -> None:
    with pytest.raises(
        ValueError,
        match="Simulation event sequence cannot be negative",
    ):
        SimulationEvent(
            sequence=-1,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=make_payment().created_at,
        )


def test_simulation_rejects_non_contiguous_event_sequences() -> None:
    order = make_order()
    payment = Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
    )

    events = (
        SimulationEvent(
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=payment.created_at,
        ),
        SimulationEvent(
            sequence=2,
            event=PaymentEvent.CAPTURE,
            occurred_at=payment.created_at,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Simulation event sequences must be contiguous and ordered",
    ):
        PaymentSimulation(
            seed=42,
            initial_payment=payment,
            initial_order=order,
            events=events,
        )


def test_simulation_event_is_immutable() -> None:
    event = SimulationEvent(
        sequence=0,
        event=PaymentEvent.AUTHORIZE,
        occurred_at=make_payment().created_at,
    )

    with pytest.raises(FrozenInstanceError):
        event.sequence = 99


def test_simulation_snapshot_is_immutable() -> None:
    payment = make_payment()
    order = make_order()

    snapshot = SimulationStateSnapshot(
        sequence=0,
        occurred_at=payment.created_at,
        payment=payment,
        order=order,
    )

    with pytest.raises(FrozenInstanceError):
        snapshot.sequence = 99


def test_trace_entry_is_immutable() -> None:
    payment = make_payment()
    order = make_order()

    trace = SimulationTraceEntry(
        sequence=0,
        event=PaymentEvent.AUTHORIZE,
        occurred_at=payment.created_at,
        payment_before=payment,
        payment_after=payment,
        order_before=order,
        order_after=order,
    )

    with pytest.raises(FrozenInstanceError):
        trace.sequence = 99


def test_payment_amount_and_currency_are_constructed_as_invariants() -> None:
    payment = make_payment()

    assert payment.amount_minor > 0
    assert len(payment.currency) == 3


def test_order_amount_and_currency_are_constructed_as_invariants() -> None:
    order = make_order()

    assert order.amount_minor > 0
    assert len(order.currency) == 3
