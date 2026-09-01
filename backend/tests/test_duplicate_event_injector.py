from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent
from app.domain.models.adversarial_simulation import AdversarialSimulation
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.services.duplicate_event_injector import DuplicateEventInjector


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


def test_duplicate_event_injection_preserves_source() -> None:
    simulation = make_simulation()

    result = DuplicateEventInjector.inject(simulation, 0)

    assert isinstance(result, AdversarialSimulation)
    assert result.source_simulation is simulation


def test_duplicate_event_is_inserted_after_target() -> None:
    simulation = make_simulation()

    result = DuplicateEventInjector.inject(simulation, 0)

    assert [event.sequence for event in result.simulation.events] == [0, 1, 2]
    assert [event.event for event in result.simulation.events] == [
        PaymentEvent.AUTHORIZE,
        PaymentEvent.AUTHORIZE,
        PaymentEvent.CAPTURE,
    ]


def test_duplicate_event_preserves_delivery_timestamp() -> None:
    simulation = make_simulation()

    result = DuplicateEventInjector.inject(simulation, 0)

    assert (
        result.simulation.events[1].occurred_at
        == result.simulation.events[0].occurred_at
    )


def test_duplicate_event_gets_distinct_identity() -> None:
    simulation = make_simulation()

    result = DuplicateEventInjector.inject(simulation, 0)

    assert result.simulation.events[0].id != result.simulation.events[1].id


def test_duplicate_event_attack_records_target() -> None:
    simulation = make_simulation()

    result = DuplicateEventInjector.inject(simulation, 0)

    assert result.attack.simulation_id == simulation.id
    assert result.attack.target_sequence == 0


def test_duplicate_event_rejects_negative_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(ValueError, match="negative"):
        DuplicateEventInjector.inject(simulation, -1)


def test_duplicate_event_rejects_unknown_sequence() -> None:
    simulation = make_simulation()

    with pytest.raises(IndexError, match="outside"):
        DuplicateEventInjector.inject(simulation, 99)


def test_duplicate_event_preserves_simulation_identity_and_seed() -> None:
    simulation = make_simulation()

    result = DuplicateEventInjector.inject(simulation, 0)

    assert result.simulation.id == simulation.id
    assert result.simulation.seed == simulation.seed
    assert result.simulation.initial_payment == simulation.initial_payment
    assert result.simulation.initial_order == simulation.initial_order
