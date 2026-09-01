from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent
from app.domain.models.partial_failure import PartialFailureScenario
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.services.partial_failure_injector import PartialFailureInjector


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


def test_partial_failure_creates_scenario() -> None:
    simulation = make_simulation()

    result = PartialFailureInjector.inject(simulation, 1)

    assert isinstance(result, PartialFailureScenario)


def test_partial_failure_targets_event() -> None:
    simulation = make_simulation()

    result = PartialFailureInjector.inject(simulation, 1)

    assert result.simulation_id == simulation.id
    assert result.target_sequence == 1


def test_partial_failure_represents_started_operation() -> None:
    simulation = make_simulation()

    result = PartialFailureInjector.inject(simulation, 1)

    assert result.operation_started is True
    assert result.operation_completed is False


def test_partial_failure_does_not_mutate_simulation() -> None:
    simulation = make_simulation()
    original_events = simulation.events

    PartialFailureInjector.inject(simulation, 1)

    assert simulation.events == original_events


def test_partial_failure_rejects_negative_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="negative"):
        PartialFailureInjector.inject(simulation, -1)


def test_partial_failure_rejects_unknown_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(IndexError, match="outside"):
        PartialFailureInjector.inject(simulation, 99)
