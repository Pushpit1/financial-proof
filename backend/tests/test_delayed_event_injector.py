from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent
from app.domain.models.adversarial_simulation import (
    AdversarialSimulation,
    DelayedEventAttack,
)
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.services.delayed_event_injector import DelayedEventInjector


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
            SimulationEvent(
                sequence=2,
                event=PaymentEvent.REFUND,
                occurred_at=timestamp.replace(second=2),
            ),
        ),
    )


def test_delayed_event_preserves_source() -> None:
    simulation = make_simulation()

    result = DelayedEventInjector.inject(
        simulation,
        target_sequence=0,
        delay_seconds=30,
    )

    assert isinstance(result, AdversarialSimulation)
    assert result.source_simulation is simulation


def test_delayed_event_moves_later() -> None:
    simulation = make_simulation()

    result = DelayedEventInjector.inject(
        simulation,
        target_sequence=0,
        delay_seconds=30,
    )

    assert [event.event for event in result.simulation.events] == [
        PaymentEvent.CAPTURE,
        PaymentEvent.AUTHORIZE,
        PaymentEvent.REFUND,
    ]


def test_delayed_event_keeps_original_occurrence_time() -> None:
    simulation = make_simulation()

    result = DelayedEventInjector.inject(
        simulation,
        target_sequence=0,
        delay_seconds=30,
    )

    assert (
        result.simulation.events[1].occurred_at
        == simulation.events[0].occurred_at
    )


def test_delayed_event_keeps_identity() -> None:
    simulation = make_simulation()

    result = DelayedEventInjector.inject(
        simulation,
        target_sequence=0,
        delay_seconds=30,
    )

    assert result.simulation.events[1].id == simulation.events[0].id


def test_delayed_attack_records_delay() -> None:
    simulation = make_simulation()

    result = DelayedEventInjector.inject(
        simulation,
        target_sequence=0,
        delay_seconds=30,
    )

    assert isinstance(result.attack, DelayedEventAttack)
    assert result.attack.target_sequence == 0
    assert result.attack.delivery_delay_seconds == 30


def test_delayed_event_preserves_seed_and_initial_state() -> None:
    simulation = make_simulation()

    result = DelayedEventInjector.inject(
        simulation,
        target_sequence=0,
        delay_seconds=30,
    )

    assert result.simulation.seed == simulation.seed
    assert result.simulation.initial_payment == simulation.initial_payment
    assert result.simulation.initial_order == simulation.initial_order


def test_delayed_event_rejects_negative_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="negative"):
        DelayedEventInjector.inject(
            simulation,
            target_sequence=-1,
            delay_seconds=30,
        )


def test_delayed_event_rejects_zero_delay() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="positive"):
        DelayedEventInjector.inject(
            simulation,
            target_sequence=0,
            delay_seconds=0,
        )


def test_delayed_event_rejects_unknown_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(IndexError, match="outside"):
        DelayedEventInjector.inject(
            simulation,
            target_sequence=99,
            delay_seconds=30,
        )
