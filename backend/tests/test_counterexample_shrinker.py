from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.enums.payment import PaymentEvent
from app.domain.models.counterexample import Counterexample
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.services.counterexample_shrinker import CounterexampleShrinker


def make_simulation(events: tuple[PaymentEvent, ...]) -> PaymentSimulation:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    simulation_events = tuple(
        SimulationEvent(
            sequence=index,
            event=event,
            occurred_at=start.replace(second=index),
        )
        for index, event in enumerate(events)
    )

    return PaymentSimulation(
        seed=42,
        initial_payment=Payment(
            order_id=uuid4(),
            amount_minor=1000,
            currency="INR",
        ),
        initial_order=PaymentOrder(
            amount_minor=1000,
            currency="INR",
        ),
        events=simulation_events,
    )


def make_counterexample(
    events: tuple[PaymentEvent, ...],
    violation_code: str = "target_violation",
) -> Counterexample:
    simulation = make_simulation(events)

    return Counterexample(
        simulation_id=simulation.id,
        simulation=simulation,
        violation_code=violation_code,
        original_event_count=len(events),
        minimized_event_count=len(events),
    )


def test_shrinker_removes_events_that_are_not_required() -> None:
    counterexample = make_counterexample(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
            PaymentEvent.REFUND,
        )
    )

    def violation(simulation: PaymentSimulation) -> bool:
        return PaymentEvent.CAPTURE in tuple(
            event.event for event in simulation.events
        )

    shrunk = CounterexampleShrinker.shrink(
        counterexample,
        violation,
    )

    assert shrunk.violation_code == "target_violation"
    assert shrunk.original_event_count == 3
    assert shrunk.minimized_event_count == 1
    assert tuple(event.event for event in shrunk.simulation.events) == (
        PaymentEvent.CAPTURE,
    )


def test_shrinker_rebuilds_contiguous_sequences() -> None:
    counterexample = make_counterexample(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
            PaymentEvent.REFUND,
        )
    )

    def violation(simulation: PaymentSimulation) -> bool:
        return PaymentEvent.REFUND in tuple(
            event.event for event in simulation.events
        )

    shrunk = CounterexampleShrinker.shrink(
        counterexample,
        violation,
    )

    assert [event.sequence for event in shrunk.simulation.events] == [0]
    assert shrunk.simulation.events[0].event is PaymentEvent.REFUND


def test_shrinker_preserves_same_violation_code() -> None:
    counterexample = make_counterexample(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
        ),
        violation_code="capture_present",
    )

    def violation(simulation: PaymentSimulation) -> bool:
        return any(
            event.event is PaymentEvent.CAPTURE
            for event in simulation.events
        )

    shrunk = CounterexampleShrinker.shrink(
        counterexample,
        violation,
    )

    assert shrunk.violation_code == "capture_present"
    assert shrunk.minimized_event_count == 1


def test_shrinker_rejects_non_failing_counterexample() -> None:
    counterexample = make_counterexample(
        (PaymentEvent.AUTHORIZE,)
    )

    with pytest.raises(
        ValueError,
        match="does not reproduce its violation",
    ):
        CounterexampleShrinker.shrink(
            counterexample,
            lambda simulation: False,
        )


def test_shrinker_is_deterministic() -> None:
    events = (
        PaymentEvent.AUTHORIZE,
        PaymentEvent.CAPTURE,
        PaymentEvent.REFUND,
        PaymentEvent.FAIL,
    )

    first = make_counterexample(events)
    second = make_counterexample(events)

    def violation(simulation: PaymentSimulation) -> bool:
        return PaymentEvent.REFUND in tuple(
            event.event for event in simulation.events
        )

    first_result = CounterexampleShrinker.shrink(first, violation)
    second_result = CounterexampleShrinker.shrink(second, violation)

    assert first_result.violation_code == second_result.violation_code
    assert first_result.original_event_count == second_result.original_event_count
    assert first_result.minimized_event_count == second_result.minimized_event_count
    assert [
        (event.sequence, event.event, event.occurred_at)
        for event in first_result.simulation.events
    ] == [
        (event.sequence, event.event, event.occurred_at)
        for event in second_result.simulation.events
    ]

def test_shrinker_reports_reduction_metrics() -> None:
    counterexample = make_counterexample(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
            PaymentEvent.REFUND,
            PaymentEvent.FAIL,
        )
    )

    def violation(simulation: PaymentSimulation) -> bool:
        return PaymentEvent.REFUND in tuple(
            event.event for event in simulation.events
        )

    result = CounterexampleShrinker.shrink_with_metrics(
        counterexample,
        violation,
    )

    assert result.reproduces_violation is True
    assert result.metrics.original_event_count == 4
    assert result.metrics.minimized_event_count == 1
    assert result.metrics.removed_event_count == 3
    assert result.metrics.reduction_ratio == 0.75
    assert result.metrics.candidate_count == 4
    assert result.metrics.reproduction_checks == 6


def test_shrinker_proves_minimized_counterexample_reproduces() -> None:
    counterexample = make_counterexample(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
        )
    )

    def violation(simulation: PaymentSimulation) -> bool:
        return PaymentEvent.CAPTURE in tuple(
            event.event for event in simulation.events
        )

    result = CounterexampleShrinker.shrink_with_metrics(
        counterexample,
        violation,
    )

    assert result.reproduces_violation is True
    assert result.counterexample.minimized_event_count == 1


def test_shrinker_result_is_deterministic_for_same_input() -> None:
    events = (
        PaymentEvent.AUTHORIZE,
        PaymentEvent.CAPTURE,
        PaymentEvent.REFUND,
    )

    counterexample = make_counterexample(events)

    def violation(simulation: PaymentSimulation) -> bool:
        return PaymentEvent.REFUND in tuple(
            event.event for event in simulation.events
        )

    first = CounterexampleShrinker.shrink_with_metrics(
        counterexample,
        violation,
    )
    second = CounterexampleShrinker.shrink_with_metrics(
        counterexample,
        violation,
    )

    assert first.metrics.original_event_count == second.metrics.original_event_count
    assert first.metrics.minimized_event_count == second.metrics.minimized_event_count
    assert first.metrics.candidate_count == second.metrics.candidate_count
    assert first.metrics.reproduction_checks == second.metrics.reproduction_checks
    assert first.metrics.reduction_ratio == second.metrics.reduction_ratio
    assert first.reproduces_violation is True
    assert second.reproduces_violation is True
