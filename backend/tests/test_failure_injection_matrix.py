from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent, PaymentState
from app.domain.models.adversarial_scenario import AdversarialScenario
from app.domain.models.adversarial_simulation import (
    DuplicateEventAttack,
    OutOfOrderEventAttack,
)
from app.domain.models.lost_response import LostResponseScenario
from app.domain.models.partial_failure import PartialFailureScenario
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.models.retry import RetryScenario
from app.domain.models.stale_worker_state import StaleWorkerStateAttack
from app.domain.models.worker_crash import WorkerCrashScenario
from app.domain.services.adversarial_scenario_executor import (
    AdversarialScenarioExecutor,
)

TIMESTAMP = datetime(2026, 8, 31, tzinfo=UTC)


def make_simulation() -> PaymentSimulation:
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
                occurred_at=TIMESTAMP,
            ),
            SimulationEvent(
                sequence=1,
                event=PaymentEvent.CAPTURE,
                occurred_at=TIMESTAMP,
            ),
        ),
    )


def execute(
    simulation: PaymentSimulation,
    component: object,
):
    scenario = AdversarialScenario(
        simulation_id=simulation.id,
        components=(component,),
    )
    return AdversarialScenarioExecutor.execute(simulation, scenario)


@pytest.mark.parametrize(
    "component_factory",
    [
        lambda simulation: LostResponseScenario(
            simulation_id=simulation.id,
            target_sequence=0,
        ),
        lambda simulation: RetryScenario(
            simulation_id=simulation.id,
            target_sequence=0,
            retry_count=1,
        ),
        lambda simulation: PartialFailureScenario(
            simulation_id=simulation.id,
            target_sequence=0,
        ),
        lambda simulation: StaleWorkerStateAttack(
            simulation_id=simulation.id,
            worker_sequence=1,
            incoming_sequence=0,
        ),
        lambda simulation: WorkerCrashScenario(
            simulation_id=simulation.id,
            target_sequence=0,
        ),
    ],
)
def test_semantic_failure_matrix_preserves_event_stream(
    component_factory,
) -> None:
    simulation = make_simulation()
    component = component_factory(simulation)

    result = execute(simulation, component)

    assert result.adversarial_simulation.events == simulation.events
    assert result.baseline.final_payment.state is PaymentState.CAPTURED
    assert result.baseline.final_order.state.name == "CAPTURED"
    assert result.adversarial_result.final_payment.state is PaymentState.CAPTURED
    assert result.adversarial_result.final_order.state.name == "CAPTURED"


@pytest.mark.parametrize(
    "component_factory",
    [
        lambda simulation: LostResponseScenario(
            simulation_id=simulation.id,
            target_sequence=0,
        ),
        lambda simulation: RetryScenario(
            simulation_id=simulation.id,
            target_sequence=0,
            retry_count=3,
        ),
        lambda simulation: PartialFailureScenario(
            simulation_id=simulation.id,
            target_sequence=0,
        ),
        lambda simulation: WorkerCrashScenario(
            simulation_id=simulation.id,
            target_sequence=0,
        ),
    ],
)
def test_semantic_failure_matrix_records_exact_component_type(
    component_factory,
) -> None:
    simulation = make_simulation()
    component = component_factory(simulation)

    result = execute(simulation, component)

    assert len(result.outcomes) == 1
    assert result.outcomes[0].component_type == type(component).__name__
    assert result.outcomes[0].target_sequence == 0
    assert result.outcomes[0].status == "applied"


def test_retry_failure_matrix_preserves_retry_metadata() -> None:
    simulation = make_simulation()

    component = RetryScenario(
        simulation_id=simulation.id,
        target_sequence=0,
        retry_count=3,
    )

    result = execute(simulation, component)

    assert result.scenario.components == (component,)
    assert result.adversarial_simulation.events == simulation.events


def test_stale_worker_failure_matrix_preserves_sequence_metadata() -> None:
    simulation = make_simulation()

    component = StaleWorkerStateAttack(
        simulation_id=simulation.id,
        worker_sequence=1,
        incoming_sequence=0,
    )

    result = execute(simulation, component)

    assert result.outcomes[0].component_type == "StaleWorkerStateAttack"
    assert result.outcomes[0].target_sequence == 0
    assert result.adversarial_simulation.events == simulation.events


def test_duplicate_event_failure_changes_only_event_stream_deterministically() -> None:
    simulation = make_simulation()

    component = DuplicateEventAttack(
        simulation_id=simulation.id,
        target_sequence=0,
    )

    first = execute(simulation, component)
    second = execute(simulation, component)

    assert first.adversarial_simulation.events == second.adversarial_simulation.events
    assert len(first.adversarial_simulation.events) == (
        len(simulation.events) + 1
    )
    assert first.adversarial_simulation.events[0].event is PaymentEvent.AUTHORIZE
    assert first.adversarial_simulation.events[1].event is PaymentEvent.AUTHORIZE


def test_out_of_order_failure_changes_only_event_order_deterministically() -> None:
    simulation = make_simulation()

    component = OutOfOrderEventAttack(
        simulation_id=simulation.id,
        source_sequence=1,
        target_sequence=0,
    )

    first = execute(simulation, component)
    second = execute(simulation, component)

    assert first.adversarial_simulation.events == second.adversarial_simulation.events
    assert len(first.adversarial_simulation.events) == len(simulation.events)
    assert tuple(
        event.event for event in first.adversarial_simulation.events
    ) == (
        PaymentEvent.CAPTURE,
        PaymentEvent.AUTHORIZE,
    )


def test_failure_matrix_rejects_cross_simulation_component() -> None:
    simulation = make_simulation()
    other_simulation = make_simulation()

    component = RetryScenario(
        simulation_id=other_simulation.id,
        target_sequence=0,
        retry_count=1,
    )

    with pytest.raises(
        ValueError,
        match="All adversarial components must target the same simulation",
    ):
        AdversarialScenario(
            simulation_id=simulation.id,
            components=(component,),
        )


def test_failure_matrix_is_repeatable_for_same_seed_and_attack() -> None:
    simulation = make_simulation()

    component = PartialFailureScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )

    first = execute(simulation, component)
    second = execute(simulation, component)

    assert first.baseline == second.baseline
    assert first.adversarial_simulation == second.adversarial_simulation
    assert first.outcomes == second.outcomes
