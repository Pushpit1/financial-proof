from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.models.stale_worker_state import StaleWorkerStateAttack
from app.domain.services.stale_worker_state_injector import StaleWorkerStateInjector


def make_simulation() -> PaymentSimulation:
    timestamp = datetime(2026, 8, 31, tzinfo=UTC)

    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )
    payment = Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
    )

    return PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=(
            SimulationEvent(
                sequence=0,
                event=PaymentEvent.AUTHORIZE,
                occurred_at=timestamp,
            ),
            SimulationEvent(
                sequence=1,
                event=PaymentEvent.CAPTURE,
                occurred_at=timestamp.replace(second=1),
            ),
        ),
    )


def test_stale_worker_state_creates_attack() -> None:
    simulation = make_simulation()

    result = StaleWorkerStateInjector.inject(
        simulation,
        worker_sequence=0,
        incoming_sequence=1,
    )

    assert isinstance(result, StaleWorkerStateAttack)


def test_stale_worker_state_preserves_sequences() -> None:
    simulation = make_simulation()

    result = StaleWorkerStateInjector.inject(
        simulation,
        worker_sequence=0,
        incoming_sequence=1,
    )

    assert result.worker_sequence == 0
    assert result.incoming_sequence == 1
    assert result.simulation_id == simulation.id


def test_stale_worker_state_rejects_negative_worker_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="negative"):
        StaleWorkerStateInjector.inject(simulation, -1, 1)


def test_stale_worker_state_rejects_negative_incoming_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="negative"):
        StaleWorkerStateInjector.inject(simulation, 0, -1)


def test_stale_worker_state_rejects_unknown_incoming_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(IndexError, match="outside"):
        StaleWorkerStateInjector.inject(simulation, 0, 99)


def test_stale_worker_state_does_not_mutate_simulation() -> None:
    simulation = make_simulation()
    original_events = simulation.events

    StaleWorkerStateInjector.inject(simulation, 0, 1)

    assert simulation.events == original_events
