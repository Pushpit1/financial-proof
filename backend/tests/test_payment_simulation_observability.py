import json
from datetime import UTC, datetime
from uuid import uuid4

import structlog

from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
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


def make_simulation() -> PaymentSimulation:
    start = datetime(2026, 8, 31, tzinfo=UTC)

    return PaymentSimulation(
        seed=42,
        initial_payment=make_payment(),
        initial_order=make_order(),
        events=(
            SimulationEvent(
                sequence=0,
                event=PaymentEvent.AUTHORIZE,
                occurred_at=start,
            ),
        ),
    )


def test_simulation_runner_binds_simulation_context_and_clears_it(
    capsys,
) -> None:
    structlog.contextvars.clear_contextvars()

    simulation = make_simulation()

    PaymentSimulationRunner.run(simulation)

    assert structlog.contextvars.get_contextvars() == {}

    output = capsys.readouterr().out.splitlines()
    events = [json.loads(line) for line in output if line.strip()]

    started = next(
        event for event in events if event["event"] == "simulation_started"
    )
    completed = next(
        event
        for event in events
        if event["event"] == "simulation_completed"
    )

    expected_id = str(simulation.id)

    assert started["simulation_id"] == expected_id
    assert completed["simulation_id"] == expected_id
    assert started["seed"] == 42
    assert started["event_count"] == 1
    assert completed["trace_count"] == 1
    assert completed["snapshot_count"] == 1


def test_simulation_runner_preserves_result_identity() -> None:
    simulation = make_simulation()

    result = PaymentSimulationRunner.run(simulation)

    assert result.simulation_id == simulation.id
    assert result.seed == simulation.seed


def test_simulation_replay_emits_replay_event(capsys) -> None:
    structlog.contextvars.clear_contextvars()

    simulation = make_simulation()

    PaymentSimulationRunner.replay(simulation)

    output = capsys.readouterr().out.splitlines()
    events = [json.loads(line) for line in output if line.strip()]

    replayed = next(
        event for event in events if event["event"] == "simulation_replayed"
    )

    assert replayed["simulation_id"] == str(simulation.id)
    assert replayed["seed"] == simulation.seed
    assert replayed["event_count"] == len(simulation.events)
