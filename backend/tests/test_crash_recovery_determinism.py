from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import OrderState, PaymentEvent, PaymentState
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.services.payment_simulation_runner import PaymentSimulationRunner

TIMESTAMP = datetime(2026, 8, 31, tzinfo=UTC)


def make_simulation() -> PaymentSimulation:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )
    payment = Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
    )

    events = (
        SimulationEvent(
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=TIMESTAMP,
        ),
        SimulationEvent(
            sequence=1,
            event=PaymentEvent.CAPTURE,
            occurred_at=TIMESTAMP,
        ),
    )

    return PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=events,
    )


def test_restart_from_same_simulation_reproduces_completed_result() -> None:
    simulation = make_simulation()

    first = PaymentSimulationRunner.run(simulation)
    restarted = PaymentSimulationRunner.run(simulation)

    assert restarted == first
    assert restarted.final_payment == first.final_payment
    assert restarted.final_order == first.final_order
    assert restarted.trace == first.trace
    assert restarted.snapshots == first.snapshots


def test_replay_is_valid_recovery_boundary() -> None:
    simulation = make_simulation()

    completed = PaymentSimulationRunner.run(simulation)
    recovered = PaymentSimulationRunner.replay(simulation)

    assert PaymentSimulationRunner.replay_matches(
        simulation,
        completed,
    )
    assert recovered == completed


def test_recovery_preserves_financial_identity() -> None:
    simulation = make_simulation()

    completed = PaymentSimulationRunner.run(simulation)
    recovered = PaymentSimulationRunner.replay(simulation)

    assert recovered.simulation_id == completed.simulation_id
    assert recovered.initial_payment.id == completed.initial_payment.id
    assert recovered.initial_order.id == completed.initial_order.id
    assert recovered.final_payment.id == completed.final_payment.id
    assert recovered.final_order.id == completed.final_order.id


def test_recovery_preserves_financial_amount_and_currency() -> None:
    simulation = make_simulation()

    PaymentSimulationRunner.run(simulation)
    recovered = PaymentSimulationRunner.replay(simulation)

    assert recovered.final_payment.amount_minor == 1000
    assert recovered.final_order.amount_minor == 1000
    assert recovered.final_payment.currency == "INR"
    assert recovered.final_order.currency == "INR"


def test_recovery_does_not_add_duplicate_events() -> None:
    simulation = make_simulation()

    completed = PaymentSimulationRunner.run(simulation)
    recovered = PaymentSimulationRunner.replay(simulation)

    assert len(completed.trace) == len(simulation.events)
    assert len(recovered.trace) == len(simulation.events)
    assert len(completed.snapshots) == len(simulation.events)
    assert len(recovered.snapshots) == len(simulation.events)


def test_recovery_does_not_mutate_original_simulation() -> None:
    simulation = make_simulation()
    original = simulation

    PaymentSimulationRunner.run(simulation)
    PaymentSimulationRunner.replay(simulation)

    assert simulation == original
    assert simulation.initial_payment.state is PaymentState.CREATED
    assert simulation.initial_order.state is OrderState.CREATED
    assert len(simulation.events) == 2


def test_recovery_is_deterministic_across_multiple_restarts() -> None:
    simulation = make_simulation()

    results = tuple(
        PaymentSimulationRunner.run(simulation)
        for _ in range(5)
    )

    assert all(result == results[0] for result in results)


def test_recovery_from_failed_simulation_is_deterministic() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )
    payment = Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
    )

    simulation = PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=(
            SimulationEvent(
                sequence=0,
                event=PaymentEvent.CAPTURE,
                occurred_at=TIMESTAMP,
            ),
        ),
    )

    with pytest.raises(Exception) as first_error:
        PaymentSimulationRunner.run(simulation)

    with pytest.raises(Exception) as second_error:
        PaymentSimulationRunner.run(simulation)

    assert type(first_error.value) is type(second_error.value)
    assert str(first_error.value) == str(second_error.value)
    assert simulation.initial_payment.state is PaymentState.CREATED
    assert simulation.initial_order.state is OrderState.CREATED


def test_recovery_cannot_create_second_capture_effect() -> None:
    simulation = make_simulation()

    first = PaymentSimulationRunner.run(simulation)
    second = PaymentSimulationRunner.replay(simulation)

    assert first.final_payment.state is PaymentState.CAPTURED
    assert second.final_payment.state is PaymentState.CAPTURED
    assert len(first.trace) == 2
    assert len(second.trace) == 2

