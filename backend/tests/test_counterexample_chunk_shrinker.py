from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent, PaymentState
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)
from app.domain.services.counterexample_chunk_shrinker import (
    CounterexampleChunkShrinker,
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
        state=PaymentState.CREATED,
    )

    return PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=tuple(
            SimulationEvent(
                sequence=sequence,
                event=PaymentEvent.AUTHORIZE,
                occurred_at=timestamp.replace(second=sequence),
            )
            for sequence in range(6)
        ),
    )


def test_chunk_shrinker_removes_irrelevant_middle_events() -> None:
    simulation = make_simulation()

    def reproduces_failure(candidate: PaymentSimulation) -> bool:
        sequences = tuple(
            event.occurred_at.second
            for event in candidate.events
        )
        return 0 in sequences and 5 in sequences

    result = CounterexampleChunkShrinker.shrink(
        simulation,
        reproduces_failure,
    )

    assert len(result.events) == 2
    assert [
        event.occurred_at.second
        for event in result.events
    ] == [0, 5]


def test_chunk_shrinker_renumbers_sequences() -> None:
    simulation = make_simulation()

    result = CounterexampleChunkShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    assert [
        event.sequence for event in result.events
    ] == list(range(len(result.events)))


def test_chunk_shrinker_preserves_event_identity() -> None:
    simulation = make_simulation()

    result = CounterexampleChunkShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    original_ids = {
        event.id
        for event in simulation.events
    }
    result_ids = {
        event.id
        for event in result.events
    }

    assert result_ids <= original_ids


def test_chunk_shrinker_does_not_mutate_original() -> None:
    simulation = make_simulation()
    original_events = simulation.events

    CounterexampleChunkShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    assert simulation.events == original_events


def test_chunk_shrinker_is_deterministic() -> None:
    simulation = make_simulation()

    first = CounterexampleChunkShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )
    second = CounterexampleChunkShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    assert first == second


def test_chunk_shrinker_rejects_non_failing_input() -> None:
    simulation = make_simulation()

    with pytest.raises(
        ValueError,
        match="requires an input that reproduces the failure",
    ):
        CounterexampleChunkShrinker.shrink(
            simulation,
            lambda candidate: False,
        )


def test_chunk_shrinker_preserves_metadata() -> None:
    simulation = make_simulation()

    result = CounterexampleChunkShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    assert result.id == simulation.id
    assert result.seed == simulation.seed
    assert result.initial_payment == simulation.initial_payment
    assert result.initial_order == simulation.initial_order
