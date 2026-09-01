from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent, PaymentState
from app.domain.models.adversarial_scenario import AdversarialScenario
from app.domain.models.partial_failure import PartialFailureScenario
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.models.retry import RetryScenario
from app.domain.models.worker_crash import WorkerCrashScenario
from app.domain.services.adversarial_scenario_shrinker import (
    AdversarialScenarioShrinker,
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


def make_scenario() -> AdversarialScenario:
    simulation = make_simulation()

    return AdversarialScenario(
        simulation_id=simulation.id,
        components=(
            WorkerCrashScenario(
                simulation_id=simulation.id,
                target_sequence=0,
            ),
            PartialFailureScenario(
                simulation_id=simulation.id,
                target_sequence=1,
            ),
            RetryScenario(
                simulation_id=simulation.id,
                target_sequence=2,
                retry_count=2,
            ),
        ),
    )


def test_shrinker_removes_unnecessary_components() -> None:
    scenario = make_scenario()

    def reproduces_failure(candidate: AdversarialScenario) -> bool:
        return any(
            component.__class__.__name__ == "RetryScenario"
            for component in candidate.components
        )

    result = AdversarialScenarioShrinker.shrink(
        scenario,
        reproduces_failure,
    )

    assert len(result.components) == 1
    assert isinstance(result.components[0], RetryScenario)


def test_shrinker_preserves_relative_component_order() -> None:
    scenario = make_scenario()

    result = AdversarialScenarioShrinker.shrink(
        scenario,
        lambda candidate: len(candidate.components) >= 2,
    )

    assert [
        component.target_sequence
        for component in result.components
    ] == [1, 2]


def test_shrinker_preserves_simulation_id() -> None:
    scenario = make_scenario()

    result = AdversarialScenarioShrinker.shrink(
        scenario,
        lambda candidate: len(candidate.components) >= 1,
    )

    assert result.simulation_id == scenario.simulation_id


def test_shrinker_does_not_mutate_original() -> None:
    scenario = make_scenario()
    original_components = scenario.components

    AdversarialScenarioShrinker.shrink(
        scenario,
        lambda candidate: len(candidate.components) >= 1,
    )

    assert scenario.components == original_components


def test_shrinker_is_deterministic() -> None:
    scenario = make_scenario()

    first = AdversarialScenarioShrinker.shrink(
        scenario,
        lambda candidate: len(candidate.components) >= 1,
    )
    second = AdversarialScenarioShrinker.shrink(
        scenario,
        lambda candidate: len(candidate.components) >= 1,
    )

    assert first == second


def test_shrinker_can_reduce_already_empty_scenario() -> None:
    scenario = make_scenario()

    empty_scenario = AdversarialScenario(
        simulation_id=scenario.simulation_id,
        components=(),
    )

    result = AdversarialScenarioShrinker.shrink(
        empty_scenario,
        lambda candidate: len(candidate.components) == 0,
    )

    assert result.components == ()
    assert result.simulation_id == scenario.simulation_id


def test_shrinker_rejects_non_failing_input() -> None:
    scenario = make_scenario()

    with pytest.raises(
        ValueError,
        match="requires an input that reproduces the failure",
    ):
        AdversarialScenarioShrinker.shrink(
            scenario,
            lambda candidate: False,
        )


def test_shrinker_preserves_remaining_component_identity() -> None:
    scenario = make_scenario()
    retry = scenario.components[2]

    result = AdversarialScenarioShrinker.shrink(
        scenario,
        lambda candidate: any(
            component is retry
            for component in candidate.components
        ),
    )

    assert result.components == (retry,)

