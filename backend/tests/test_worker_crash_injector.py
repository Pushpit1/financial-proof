from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.models.worker_crash import WorkerCrashScenario
from app.domain.services.worker_crash_injector import WorkerCrashInjector


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


def test_worker_crash_creates_scenario() -> None:
    simulation = make_simulation()

    result = WorkerCrashInjector.inject(simulation, 1)

    assert isinstance(result, WorkerCrashScenario)


def test_worker_crash_targets_event() -> None:
    simulation = make_simulation()

    result = WorkerCrashInjector.inject(simulation, 1)

    assert result.simulation_id == simulation.id
    assert result.target_sequence == 1


def test_worker_crash_represents_restart() -> None:
    simulation = make_simulation()

    result = WorkerCrashInjector.inject(simulation, 1)

    assert result.restarted is True


def test_worker_crash_does_not_mutate_simulation() -> None:
    simulation = make_simulation()
    original_events = simulation.events

    WorkerCrashInjector.inject(simulation, 1)

    assert simulation.events == original_events


def test_worker_crash_rejects_negative_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="negative"):
        WorkerCrashInjector.inject(simulation, -1)


def test_worker_crash_rejects_unknown_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(IndexError, match="outside"):
        WorkerCrashInjector.inject(simulation, 99)
