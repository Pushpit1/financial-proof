from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent
from app.domain.models.adversarial_simulation import (
    AdversarialSimulation,
    OutOfOrderEventAttack,
)
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.services.out_of_order_event_injector import (
    OutOfOrderEventInjector,
)


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


def test_out_of_order_injection_preserves_source() -> None:
    simulation = make_simulation()

    result = OutOfOrderEventInjector.inject(
        simulation,
        source_sequence=2,
        target_sequence=1,
    )

    assert isinstance(result, AdversarialSimulation)
    assert result.source_simulation is simulation


def test_out_of_order_event_is_moved() -> None:
    simulation = make_simulation()

    result = OutOfOrderEventInjector.inject(
        simulation,
        source_sequence=2,
        target_sequence=1,
    )

    assert [event.event for event in result.simulation.events] == [
        PaymentEvent.AUTHORIZE,
        PaymentEvent.REFUND,
        PaymentEvent.CAPTURE,
    ]


def test_out_of_order_sequences_are_rebuilt_contiguously() -> None:
    simulation = make_simulation()

    result = OutOfOrderEventInjector.inject(
        simulation,
        source_sequence=2,
        target_sequence=1,
    )

    assert [event.sequence for event in result.simulation.events] == [0, 1, 2]


def test_out_of_order_event_keeps_identity() -> None:
    simulation = make_simulation()

    result = OutOfOrderEventInjector.inject(
        simulation,
        source_sequence=2,
        target_sequence=1,
    )

    assert result.simulation.events[1].id == simulation.events[2].id


def test_out_of_order_event_keeps_occurrence_time() -> None:
    simulation = make_simulation()

    result = OutOfOrderEventInjector.inject(
        simulation,
        source_sequence=2,
        target_sequence=1,
    )

    assert (
        result.simulation.events[1].occurred_at
        == simulation.events[2].occurred_at
    )


def test_out_of_order_attack_is_typed_correctly() -> None:
    simulation = make_simulation()

    result = OutOfOrderEventInjector.inject(
        simulation,
        source_sequence=2,
        target_sequence=1,
    )

    assert isinstance(result.attack, OutOfOrderEventAttack)
    assert result.attack.source_sequence == 2
    assert result.attack.target_sequence == 1


def test_out_of_order_preserves_seed_and_initial_state() -> None:
    simulation = make_simulation()

    result = OutOfOrderEventInjector.inject(
        simulation,
        source_sequence=2,
        target_sequence=1,
    )

    assert result.simulation.seed == simulation.seed
    assert result.simulation.initial_payment == simulation.initial_payment
    assert result.simulation.initial_order == simulation.initial_order


def test_out_of_order_rejects_negative_source() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="negative"):
        OutOfOrderEventInjector.inject(
            simulation,
            source_sequence=-1,
            target_sequence=1,
        )


def test_out_of_order_rejects_unknown_source() -> None:
    simulation = make_simulation()

    with pytest.raises(IndexError, match="outside"):
        OutOfOrderEventInjector.inject(
            simulation,
            source_sequence=99,
            target_sequence=1,
        )


def test_out_of_order_rejects_same_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="different"):
        OutOfOrderEventInjector.inject(
            simulation,
            source_sequence=1,
            target_sequence=1,
        )
