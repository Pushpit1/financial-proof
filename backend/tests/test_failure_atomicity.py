from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import OrderState, PaymentEvent, PaymentState
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.services.payment_simulation_runner import PaymentSimulationRunner
from app.domain.services.payment_state_machine import (
    InvalidOrderTransition,
    InvalidPaymentTransition,
    OrderStateMachine,
    PaymentStateMachine,
)

TIMESTAMP = datetime(2026, 8, 31, tzinfo=UTC)


def make_payment(
    state: PaymentState = PaymentState.CREATED,
) -> Payment:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )
    return Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
        state=state,
    )


def make_order(
    state: OrderState = OrderState.CREATED,
) -> PaymentOrder:
    return PaymentOrder(
        amount_minor=1000,
        currency="INR",
        state=state,
    )


def make_simulation(
    events: tuple[SimulationEvent, ...],
) -> PaymentSimulation:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )
    payment = Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
        state=PaymentState.CREATED,
    )

    return PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=events,
    )


def test_invalid_payment_transition_is_failure_atomic() -> None:
    payment = make_payment(PaymentState.AUTHORIZED)
    original = payment

    with pytest.raises(
        InvalidPaymentTransition,
        match="Cannot apply 'authorize'",
    ):
        PaymentStateMachine.transition(payment, PaymentEvent.AUTHORIZE)

    assert payment == original
    assert payment.state is PaymentState.AUTHORIZED


def test_invalid_order_transition_is_failure_atomic() -> None:
    order = make_order(OrderState.AUTHORIZED)
    original = order

    with pytest.raises(
        InvalidOrderTransition,
        match="Cannot apply 'authorize'",
    ):
        OrderStateMachine.transition(order, PaymentEvent.AUTHORIZE)

    assert order == original
    assert order.state is OrderState.AUTHORIZED


def test_valid_payment_transition_does_not_mutate_previous_record() -> None:
    payment = make_payment(PaymentState.CREATED)

    transitioned = PaymentStateMachine.transition(
        payment,
        PaymentEvent.AUTHORIZE,
    )

    assert payment.state is PaymentState.CREATED
    assert transitioned.state is PaymentState.AUTHORIZED
    assert transitioned.id == payment.id
    assert transitioned.order_id == payment.order_id
    assert transitioned.amount_minor == payment.amount_minor
    assert transitioned.currency == payment.currency


def test_valid_order_transition_does_not_mutate_previous_record() -> None:
    order = make_order(OrderState.CREATED)

    transitioned = OrderStateMachine.transition(
        order,
        PaymentEvent.AUTHORIZE,
    )

    assert order.state is OrderState.CREATED
    assert transitioned.state is OrderState.AUTHORIZED
    assert transitioned.id == order.id
    assert transitioned.amount_minor == order.amount_minor
    assert transitioned.currency == order.currency


def test_failed_transition_cannot_fabricate_captured_payment() -> None:
    payment = make_payment(PaymentState.CREATED)

    with pytest.raises(InvalidPaymentTransition):
        PaymentStateMachine.transition(payment, PaymentEvent.CAPTURE)

    assert payment.state is PaymentState.CREATED


def test_failed_transition_cannot_fabricate_captured_order() -> None:
    order = make_order(OrderState.CREATED)

    with pytest.raises(InvalidOrderTransition):
        OrderStateMachine.transition(order, PaymentEvent.CAPTURE)

    assert order.state is OrderState.CREATED


def test_simulation_failure_does_not_mutate_input_simulation() -> None:
    events = (
        SimulationEvent(
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=TIMESTAMP,
        ),
        SimulationEvent(
            sequence=1,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=TIMESTAMP,
        ),
    )
    simulation = make_simulation(events)

    original_payment = simulation.initial_payment
    original_order = simulation.initial_order
    original_events = simulation.events

    with pytest.raises(InvalidPaymentTransition):
        PaymentSimulationRunner.run(simulation)

    assert simulation.initial_payment == original_payment
    assert simulation.initial_order == original_order
    assert simulation.events == original_events


def test_same_failed_simulation_is_deterministic() -> None:
    events = (
        SimulationEvent(
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=TIMESTAMP,
        ),
        SimulationEvent(
            sequence=1,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=TIMESTAMP,
        ),
    )

    first_simulation = make_simulation(events)
    second_simulation = PaymentSimulation(
        id=first_simulation.id,
        seed=first_simulation.seed,
        initial_payment=first_simulation.initial_payment,
        initial_order=first_simulation.initial_order,
        events=first_simulation.events,
    )

    with pytest.raises(
        InvalidPaymentTransition,
    ) as first_error:
        PaymentSimulationRunner.run(first_simulation)

    with pytest.raises(
        InvalidPaymentTransition,
    ) as second_error:
        PaymentSimulationRunner.run(second_simulation)

    assert str(first_error.value) == str(second_error.value)
    assert first_simulation == second_simulation


def test_failure_after_successful_transition_preserves_last_valid_state() -> None:
    events = (
        SimulationEvent(
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=TIMESTAMP,
        ),
        SimulationEvent(
            sequence=1,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=TIMESTAMP,
        ),
    )
    simulation = make_simulation(events)

    with pytest.raises(
        InvalidPaymentTransition,
        match="Cannot apply 'authorize' to payment in state 'authorized'",
    ):
        PaymentSimulationRunner.run(simulation)

    assert simulation.initial_payment.state is PaymentState.CREATED
    assert simulation.initial_order.state is OrderState.CREATED
