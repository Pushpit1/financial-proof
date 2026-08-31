from datetime import UTC, datetime
from uuid import uuid4

from app.domain.enums.payment import OrderState, PaymentEvent, PaymentState
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)
from app.domain.services.deterministic_clock import DeterministicClock
from app.domain.services.payment_simulation_batch_runner import (
    PaymentSimulationBatchRunner,
)
from app.domain.services.payment_simulation_runner import PaymentSimulationRunner


def make_payment() -> Payment:
    return Payment(
        order_id=uuid4(),
        amount_minor=1000,
        currency="INR",
    )


def make_order() -> PaymentOrder:
    return PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )


def test_simulation_event_is_ordered() -> None:
    timestamp = datetime(2026, 8, 31, tzinfo=UTC)

    event = SimulationEvent(
        sequence=0,
        event=PaymentEvent.AUTHORIZE,
        occurred_at=timestamp,
    )

    assert event.sequence == 0
    assert event.event is PaymentEvent.AUTHORIZE
    assert event.occurred_at == timestamp


def test_simulation_rejects_non_contiguous_event_sequences() -> None:
    timestamp = datetime(2026, 8, 31, tzinfo=UTC)

    first = SimulationEvent(
        sequence=1,
        event=PaymentEvent.AUTHORIZE,
        occurred_at=timestamp,
    )

    try:
        PaymentSimulation(
            seed=42,
            initial_payment=make_payment(),
            initial_order=make_order(),
            events=(first,),
        )
    except ValueError as exc:
        assert "contiguous" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_deterministic_clock_advances_predictably() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)
    clock = DeterministicClock(start)

    assert clock.now() == start
    assert clock.advance() == datetime(
        2026,
        8,
        31,
        0,
        0,
        1,
        tzinfo=UTC,
    )


def test_deterministic_clock_rejects_negative_steps() -> None:
    clock = DeterministicClock(
        datetime(2026, 8, 31, tzinfo=UTC)
    )

    try:
        clock.advance(-1)
    except ValueError as exc:
        assert "negative" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_event_generation_is_reproducible() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    first = PaymentSimulationRunner.create_events(
        seed=123,
        event_count=10,
        start_time=start,
    )

    second = PaymentSimulationRunner.create_events(
        seed=123,
        event_count=10,
        start_time=start,
    )

    assert [event.event for event in first] == [
        event.event for event in second
    ]

    assert [event.occurred_at for event in first] == [
        event.occurred_at for event in second
    ]


def test_different_seeds_can_produce_different_sequences() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    first = PaymentSimulationRunner.create_events(
        seed=1,
        event_count=20,
        start_time=start,
    )

    second = PaymentSimulationRunner.create_events(
        seed=999,
        event_count=20,
        start_time=start,
    )

    assert [event.event for event in first] != [
        event.event for event in second
    ]


def test_simulation_runner_executes_valid_lifecycle() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    payment = make_payment()
    order = make_order()

    events = (
        SimulationEvent(
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=start,
        ),
        SimulationEvent(
            sequence=1,
            event=PaymentEvent.CAPTURE,
            occurred_at=start.replace(second=1),
        ),
        SimulationEvent(
            sequence=2,
            event=PaymentEvent.REFUND,
            occurred_at=start.replace(second=2),
        ),
    )

    simulation = PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=events,
    )

    result = PaymentSimulationRunner.run(simulation)

    assert result.seed == 42
    assert result.final_payment.state is PaymentState.REFUNDED

    # The existing M7 order state machine intentionally leaves
    # the order in CAPTURED after a payment refund.
    assert result.final_order.state is OrderState.CAPTURED

    assert len(result.trace) == 3
    assert result.trace[0].payment_before.state is PaymentState.CREATED
    assert result.trace[0].payment_after.state is PaymentState.AUTHORIZED
    assert result.trace[1].payment_after.state is PaymentState.CAPTURED
    assert result.trace[2].payment_after.state is PaymentState.REFUNDED


def test_simulation_result_is_reproducible() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    payment = make_payment()
    order = make_order()

    events = PaymentSimulationRunner.create_events(
        seed=42,
        event_count=0,
        start_time=start,
    )

    first = PaymentSimulationRunner.run(
        PaymentSimulation(
            seed=42,
            initial_payment=payment,
            initial_order=order,
            events=events,
        )
    )

    second = PaymentSimulationRunner.run(
        PaymentSimulation(
            seed=42,
            initial_payment=payment,
            initial_order=order,
            events=events,
        )
    )

    assert first.seed == second.seed
    assert first.final_payment == second.final_payment
    assert first.final_order == second.final_order
    assert first.trace == second.trace

def test_simulation_result_contains_ordered_trace_snapshots() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    payment = make_payment()
    order = make_order()

    events = (
        SimulationEvent(
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=start,
        ),
        SimulationEvent(
            sequence=1,
            event=PaymentEvent.CAPTURE,
            occurred_at=start.replace(second=1),
        ),
    )

    simulation = PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=events,
    )

    result = PaymentSimulationRunner.run(simulation)

    assert len(result.trace) == len(simulation.events)
    assert [entry.sequence for entry in result.trace] == [0, 1]

    assert result.trace[0].payment_before == payment
    assert result.trace[0].order_before == order

    assert result.snapshots[0] == (
        result.trace[0].payment_after,
        result.trace[0].order_after,
    )


def test_simulation_replay_reproduces_result() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    payment = make_payment()
    order = make_order()

    events = (
        SimulationEvent(
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=start,
        ),
        SimulationEvent(
            sequence=1,
            event=PaymentEvent.CAPTURE,
            occurred_at=start.replace(second=1),
        ),
    )

    simulation = PaymentSimulation(
        seed=123,
        initial_payment=payment,
        initial_order=order,
        events=events,
    )

    result = PaymentSimulationRunner.run(simulation)
    replayed = PaymentSimulationRunner.replay(simulation)

    assert replayed.seed == result.seed
    assert replayed.initial_payment == result.initial_payment
    assert replayed.initial_order == result.initial_order
    assert replayed.final_payment == result.final_payment
    assert replayed.final_order == result.final_order
    assert replayed.trace == result.trace


def test_simulation_replay_matches_helper() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    payment = make_payment()
    order = make_order()

    events = (
        SimulationEvent(
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=start,
        ),
    )

    simulation = PaymentSimulation(
        seed=99,
        initial_payment=payment,
        initial_order=order,
        events=events,
    )

    result = PaymentSimulationRunner.run(simulation)

    assert PaymentSimulationRunner.replay_matches(
        simulation,
        result,
    )

def test_batch_runner_executes_simulations_in_input_order() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    payment = make_payment()
    order = make_order()

    simulations = PaymentSimulationBatchRunner.build(
        seeds=(1, 2, 3),
        initial_payment=payment,
        initial_order=order,
        event_count=0,
        start_time=start,
    )

    results = PaymentSimulationBatchRunner.run(simulations)

    assert len(results) == 3
    assert [result.seed for result in results] == [1, 2, 3]
    assert [result.simulation_id for result in results] == [
        simulation.id for simulation in simulations
    ]


def test_batch_runner_replay_matches_original_results() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    payment = make_payment()
    order = make_order()

    simulations = PaymentSimulationBatchRunner.build(
        seeds=(10, 20, 30),
        initial_payment=payment,
        initial_order=order,
        event_count=0,
        start_time=start,
    )

    results = PaymentSimulationBatchRunner.run(simulations)
    replayed = PaymentSimulationBatchRunner.replay(simulations)

    assert replayed == results
    assert PaymentSimulationBatchRunner.replay_matches(
        simulations,
        results,
    )


def test_same_seed_produces_same_event_sequence() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    payment = make_payment()
    order = make_order()

    first = PaymentSimulationBatchRunner.build(
        seeds=(42,),
        initial_payment=payment,
        initial_order=order,
        event_count=10,
        start_time=start,
    )[0]

    second = PaymentSimulationBatchRunner.build(
        seeds=(42,),
        initial_payment=payment,
        initial_order=order,
        event_count=10,
        start_time=start,
    )[0]

    first_sequence = tuple(
        (event.sequence, event.event, event.occurred_at)
        for event in first.events
    )

    second_sequence = tuple(
        (event.sequence, event.event, event.occurred_at)
        for event in second.events
    )

    assert first_sequence == second_sequence

def test_different_seeds_can_produce_different_event_sequences() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    payment = make_payment()
    order = make_order()

    first = PaymentSimulationBatchRunner.build(
        seeds=(1,),
        initial_payment=payment,
        initial_order=order,
        event_count=10,
        start_time=start,
    )[0]

    second = PaymentSimulationBatchRunner.build(
        seeds=(2,),
        initial_payment=payment,
        initial_order=order,
        event_count=10,
        start_time=start,
    )[0]

    assert first.events != second.events


def test_simulation_result_contains_state_snapshots() -> None:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    payment = make_payment()
    order = make_order()

    events = (
        SimulationEvent(
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=start,
        ),
        SimulationEvent(
            sequence=1,
            event=PaymentEvent.CAPTURE,
            occurred_at=start.replace(second=1),
        ),
    )

    simulation = PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=events,
    )

    result = PaymentSimulationRunner.run(simulation)

    assert len(result.snapshots) == len(events)
    assert result.snapshots[0].sequence == 0
    assert result.snapshots[-1].sequence == 1
    assert result.snapshots[-1].payment == result.final_payment
    assert result.snapshots[-1].order == result.final_order
