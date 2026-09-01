from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent, PaymentState
from app.domain.models.adversarial_scenario import AdversarialScenario
from app.domain.models.lost_response import LostResponseScenario
from app.domain.models.partial_failure import PartialFailureScenario
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.models.retry import RetryScenario
from app.domain.models.stale_worker_state import StaleWorkerStateAttack
from app.domain.models.worker_crash import WorkerCrashScenario


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
                event=PaymentEvent.CAPTURE,
                occurred_at=timestamp.replace(second=2),
            ),
        ),
    )


def test_empty_scenario_is_valid() -> None:
    from app.domain.services.adversarial_scenario_composer import (
        AdversarialScenarioComposer,
    )

    simulation = make_simulation()

    scenario = AdversarialScenarioComposer.compose(simulation)

    assert isinstance(scenario, AdversarialScenario)
    assert scenario.simulation_id == simulation.id
    assert scenario.components == ()


def test_components_are_deterministically_ordered() -> None:
    from app.domain.services.adversarial_scenario_composer import (
        AdversarialScenarioComposer,
    )

    simulation = make_simulation()

    worker_crash = WorkerCrashScenario(
        simulation_id=simulation.id,
        target_sequence=2,
    )
    retry = RetryScenario(
        simulation_id=simulation.id,
        target_sequence=0,
        retry_count=2,
    )
    partial_failure = PartialFailureScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )

    first = AdversarialScenarioComposer.compose(
        simulation,
        worker_crash,
        retry,
        partial_failure,
    )
    second = AdversarialScenarioComposer.compose(
        simulation,
        partial_failure,
        worker_crash,
        retry,
    )

    assert first.components == second.components
    assert [
        component.target_sequence for component in first.components
    ] == [0, 1, 2]


def test_different_simulation_is_rejected() -> None:
    from app.domain.services.adversarial_scenario_composer import (
        AdversarialScenarioComposer,
    )

    simulation = make_simulation()

    other_order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )
    other_payment = Payment(
        order_id=other_order.id,
        amount_minor=1000,
        currency="INR",
    )
    other_simulation = PaymentSimulation(
        seed=99,
        initial_payment=other_payment,
        initial_order=other_order,
    )

    component = LostResponseScenario(
        simulation_id=other_simulation.id,
        target_sequence=0,
    )

    with pytest.raises(ValueError, match="different simulation"):
        AdversarialScenarioComposer.compose(
            simulation,
            component,
        )


def test_duplicate_target_sequence_is_rejected() -> None:
    simulation = make_simulation()

    first = WorkerCrashScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )
    second = PartialFailureScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )

    with pytest.raises(ValueError, match="same sequence"):
        AdversarialScenario(
            simulation_id=simulation.id,
            components=(first, second),
        )


def test_stale_worker_state_rejects_newer_incoming_sequence() -> None:
    simulation = make_simulation()

    component = StaleWorkerStateAttack(
        simulation_id=simulation.id,
        worker_sequence=1,
        incoming_sequence=2,
    )

    with pytest.raises(
        ValueError,
        match="newer than worker state",
    ):
        AdversarialScenario(
            simulation_id=simulation.id,
            components=(component,),
        )


def test_stale_worker_state_can_be_composed() -> None:
    simulation = make_simulation()

    component = StaleWorkerStateAttack(
        simulation_id=simulation.id,
        worker_sequence=2,
        incoming_sequence=1,
    )

    scenario = AdversarialScenario(
        simulation_id=simulation.id,
        components=(component,),
    )

    assert scenario.components == (component,)


def test_scenario_is_immutable() -> None:
    simulation = make_simulation()

    scenario = AdversarialScenario(
        simulation_id=simulation.id,
        components=(),
    )

    with pytest.raises(AttributeError):
        scenario.simulation_id = simulation.id


def test_composition_does_not_mutate_simulation() -> None:
    from app.domain.services.adversarial_scenario_composer import (
        AdversarialScenarioComposer,
    )

    simulation = make_simulation()
    original_events = simulation.events

    AdversarialScenarioComposer.compose(
        simulation,
        LostResponseScenario(
            simulation_id=simulation.id,
            target_sequence=0,
        ),
        RetryScenario(
            simulation_id=simulation.id,
            target_sequence=1,
            retry_count=2,
        ),
    )

    assert simulation.events == original_events
