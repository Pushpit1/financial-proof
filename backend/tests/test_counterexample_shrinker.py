from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent, PaymentState
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)
from app.domain.services.counterexample_shrinker import CounterexampleShrinker


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
        state=PaymentState.CREATED,
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


def test_shrinker_removes_events_while_failure_survives() -> None:
    simulation = make_simulation()

    def reproduces_failure(candidate: PaymentSimulation) -> bool:
        return len(candidate.events) >= 2

    result = CounterexampleShrinker.shrink(
        simulation,
        reproduces_failure,
    )

    assert len(result.events) == 2
    assert [event.sequence for event in result.events] == [0, 1]


def test_shrinker_returns_minimal_single_event_failure() -> None:
    simulation = make_simulation()

    result = CounterexampleShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 1,
    )

    assert len(result.events) == 1
    assert result.events[0].sequence == 0
    assert result.events[0].event is PaymentEvent.AUTHORIZE


def test_shrinker_preserves_simulation_identity_and_metadata() -> None:
    simulation = make_simulation()

    result = CounterexampleShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    assert result.id == simulation.id
    assert result.seed == simulation.seed
    assert result.initial_payment == simulation.initial_payment
    assert result.initial_order == simulation.initial_order


def test_shrinker_preserves_event_identity_and_timestamps() -> None:
    simulation = make_simulation()

    result = CounterexampleShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    assert result.events[0].id == simulation.events[0].id
    assert result.events[1].id == simulation.events[1].id
    assert result.events[0].occurred_at == simulation.events[0].occurred_at
    assert result.events[1].occurred_at == simulation.events[1].occurred_at


def test_shrinker_does_not_mutate_original_simulation() -> None:
    simulation = make_simulation()
    original_events = simulation.events

    CounterexampleShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 1,
    )

    assert simulation.events == original_events


def test_shrinker_is_deterministic() -> None:
    simulation = make_simulation()

    first = CounterexampleShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )
    second = CounterexampleShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    assert first == second


def test_shrinker_rejects_non_failing_input() -> None:
    simulation = make_simulation()

    with pytest.raises(
        ValueError,
        match="requires an input that reproduces the failure",
    ):
        CounterexampleShrinker.shrink(
            simulation,
            lambda candidate: False,
        )


def test_shrinker_accepts_already_minimal_empty_simulation() -> None:
    simulation = make_simulation()

    empty_simulation = PaymentSimulation(
        seed=simulation.seed,
        initial_payment=simulation.initial_payment,
        initial_order=simulation.initial_order,
        events=(),
        id=simulation.id,
    )

    result = CounterexampleShrinker.shrink(
        empty_simulation,
        lambda candidate: len(candidate.events) == 0,
    )

    assert result.events == ()
    assert result.id == simulation.id
