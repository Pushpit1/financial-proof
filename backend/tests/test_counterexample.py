from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.enums.payment import PaymentEvent
from app.domain.models.counterexample import Counterexample
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent


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


def test_counterexample_captures_failing_simulation() -> None:
    simulation = make_simulation(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
        )
    )

    counterexample = Counterexample(
        simulation_id=simulation.id,
        simulation=simulation,
        violation_code="duplicate_charge",
        original_event_count=2,
        minimized_event_count=2,
    )

    assert counterexample.simulation_id == simulation.id
    assert counterexample.simulation == simulation
    assert counterexample.violation_code == "duplicate_charge"
    assert counterexample.original_event_count == 2
    assert counterexample.minimized_event_count == 2


def test_counterexample_is_immutable() -> None:
    simulation = make_simulation((PaymentEvent.AUTHORIZE,))

    counterexample = Counterexample(
        simulation_id=simulation.id,
        simulation=simulation,
        violation_code="duplicate_charge",
        original_event_count=1,
        minimized_event_count=1,
    )

    with pytest.raises(AttributeError):
        counterexample.violation_code = "changed"  # type: ignore[misc]


def test_counterexample_requires_matching_simulation_id() -> None:
    simulation = make_simulation((PaymentEvent.AUTHORIZE,))

    with pytest.raises(
        ValueError,
        match="simulation_id must match simulation.id",
    ):
        Counterexample(
            simulation_id=uuid4(),
            simulation=simulation,
            violation_code="duplicate_charge",
            original_event_count=1,
            minimized_event_count=1,
        )


def test_counterexample_rejects_empty_violation_code() -> None:
    simulation = make_simulation((PaymentEvent.AUTHORIZE,))

    with pytest.raises(
        ValueError,
        match="violation_code cannot be empty",
    ):
        Counterexample(
            simulation_id=simulation.id,
            simulation=simulation,
            violation_code="   ",
            original_event_count=1,
            minimized_event_count=1,
        )


def test_counterexample_allows_minimized_simulation_to_be_smaller() -> None:
    simulation = make_simulation((PaymentEvent.AUTHORIZE,))

    counterexample = Counterexample(
        simulation_id=simulation.id,
        simulation=simulation,
        violation_code="duplicate_charge",
        original_event_count=3,
        minimized_event_count=1,
    )

    assert counterexample.original_event_count == 3
    assert counterexample.minimized_event_count == 1


def test_counterexample_rejects_invalid_event_counts() -> None:
    simulation = make_simulation(
        (
            PaymentEvent.AUTHORIZE,
            PaymentEvent.CAPTURE,
        )
    )

    with pytest.raises(
        ValueError,
        match="minimized_event_count cannot exceed",
    ):
        Counterexample(
            simulation_id=simulation.id,
            simulation=simulation,
            violation_code="duplicate_charge",
            original_event_count=1,
            minimized_event_count=2,
        )

    with pytest.raises(
        ValueError,
        match="minimized_event_count must match",
    ):
        Counterexample(
            simulation_id=simulation.id,
            simulation=simulation,
            violation_code="duplicate_charge",
            original_event_count=2,
            minimized_event_count=1,
        )
