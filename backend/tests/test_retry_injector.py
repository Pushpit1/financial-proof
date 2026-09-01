from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.models.retry import RetryScenario
from app.domain.services.retry_injector import RetryInjector


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


def test_retry_creates_scenario() -> None:
    simulation = make_simulation()

    result = RetryInjector.inject(simulation, 1)

    assert isinstance(result, RetryScenario)


def test_retry_targets_requested_event() -> None:
    simulation = make_simulation()

    result = RetryInjector.inject(
        simulation,
        target_sequence=1,
        retry_count=2,
    )

    assert result.simulation_id == simulation.id
    assert result.target_sequence == 1
    assert result.retry_count == 2


def test_retry_does_not_mutate_simulation() -> None:
    simulation = make_simulation()
    original_events = simulation.events

    RetryInjector.inject(simulation, 1, retry_count=2)

    assert simulation.events == original_events


def test_retry_preserves_simulation_identity() -> None:
    simulation = make_simulation()

    result = RetryInjector.inject(simulation, 1)

    assert result.simulation_id == simulation.id


def test_retry_supports_multiple_attempts() -> None:
    simulation = make_simulation()

    result = RetryInjector.inject(
        simulation,
        target_sequence=1,
        retry_count=3,
    )

    assert result.retry_count == 3


def test_retry_rejects_negative_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="negative"):
        RetryInjector.inject(simulation, -1)


def test_retry_rejects_zero_retry_count() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="positive"):
        RetryInjector.inject(simulation, 1, retry_count=0)


def test_retry_rejects_unknown_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(IndexError, match="outside"):
        RetryInjector.inject(simulation, 99)
