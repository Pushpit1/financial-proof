from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent, PaymentState
from app.domain.models.adversarial_scenario import AdversarialScenario
from app.domain.models.adversarial_simulation import DuplicateEventAttack
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.models.retry import RetryScenario
from app.domain.services.adversarial_scenario_executor import (
    AdversarialScenarioExecutor,
)
from app.domain.services.payment_state_machine import InvalidPaymentTransition

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


def test_retry_replay_does_not_mutate_original_simulation() -> None:
    simulation = make_simulation()
    original_events = simulation.events
    original_payment = simulation.initial_payment
    original_order = simulation.initial_order

    component = RetryScenario(
        simulation_id=simulation.id,
        target_sequence=0,
        retry_count=3,
    )

    result = execute(simulation, component)

    assert simulation.events == original_events
    assert simulation.initial_payment == original_payment
    assert simulation.initial_order == original_order
    assert result.adversarial_simulation == simulation


def test_same_retry_replay_is_deterministic() -> None:
    simulation = make_simulation()

    component = RetryScenario(
        simulation_id=simulation.id,
        target_sequence=0,
        retry_count=3,
    )

    first = execute(simulation, component)
    second = execute(simulation, component)

    assert first == second
    assert first.baseline == second.baseline
    assert first.adversarial_simulation == second.adversarial_simulation
    assert first.outcomes == second.outcomes


def test_retry_replay_preserves_single_financial_effect() -> None:
    simulation = make_simulation()

    component = RetryScenario(
        simulation_id=simulation.id,
        target_sequence=0,
        retry_count=5,
    )

    result = execute(simulation, component)

    assert len(result.adversarial_simulation.events) == len(simulation.events)
    assert result.adversarial_result.final_payment.state is PaymentState.CAPTURED
    assert result.adversarial_result.final_order.state.name == "CAPTURED"
    assert result.adversarial_result.final_payment.amount_minor == 1000
    assert result.adversarial_result.final_order.amount_minor == 1000


def test_retry_replay_preserves_financial_identity() -> None:
    simulation = make_simulation()

    component = RetryScenario(
        simulation_id=simulation.id,
        target_sequence=1,
        retry_count=2,
    )

    result = execute(simulation, component)

    assert result.adversarial_result.final_payment.id == simulation.initial_payment.id
    assert result.adversarial_result.final_payment.order_id == (
        simulation.initial_payment.order_id
    )
    assert result.adversarial_result.final_payment.currency == "INR"
    assert result.adversarial_result.final_order.id == simulation.initial_order.id
    assert result.adversarial_result.final_order.currency == "INR"


def test_retry_count_is_preserved_as_attack_identity() -> None:
    simulation = make_simulation()

    retry_once = RetryScenario(
        simulation_id=simulation.id,
        target_sequence=0,
        retry_count=1,
    )
    retry_three = RetryScenario(
        simulation_id=simulation.id,
        target_sequence=0,
        retry_count=3,
    )

    first = execute(simulation, retry_once)
    second = execute(simulation, retry_three)

    assert first.scenario.components == (retry_once,)
    assert second.scenario.components == (retry_three,)
    assert first.scenario.components != second.scenario.components
    assert first.adversarial_simulation.events == simulation.events
    assert second.adversarial_simulation.events == simulation.events


def test_replay_of_duplicate_event_fails_deterministically() -> None:
    simulation = make_simulation()

    component = DuplicateEventAttack(
        simulation_id=simulation.id,
        target_sequence=0,
    )

    with pytest.raises(
        InvalidPaymentTransition,
        match="Cannot apply 'authorize' to payment in state 'authorized'",
    ):
        result = execute(simulation, component)
        _ = result.adversarial_result

    with pytest.raises(
        InvalidPaymentTransition,
        match="Cannot apply 'authorize' to payment in state 'authorized'",
    ):
        result = execute(simulation, component)
        _ = result.adversarial_result


def test_duplicate_replay_cannot_create_a_second_financial_effect() -> None:
    simulation = make_simulation()

    component = DuplicateEventAttack(
        simulation_id=simulation.id,
        target_sequence=0,
    )

    original_events = simulation.events
    original_payment = simulation.initial_payment
    original_order = simulation.initial_order

    with pytest.raises(InvalidPaymentTransition):
        result = execute(simulation, component)
        _ = result.adversarial_result

    assert simulation.events == original_events
    assert simulation.initial_payment == original_payment
    assert simulation.initial_order == original_order


def test_retry_replay_outcome_is_explicitly_recorded() -> None:
    simulation = make_simulation()

    component = RetryScenario(
        simulation_id=simulation.id,
        target_sequence=0,
        retry_count=4,
    )

    result = execute(simulation, component)

    assert len(result.outcomes) == 1
    assert result.outcomes[0].component_type == "RetryScenario"
    assert result.outcomes[0].target_sequence == 0
    assert result.outcomes[0].status == "applied"


def test_replay_same_seed_same_attack_produces_same_financial_result() -> None:
    first_simulation = make_simulation()
    second_simulation = PaymentSimulation(
        id=first_simulation.id,
        seed=first_simulation.seed,
        initial_payment=first_simulation.initial_payment,
        initial_order=first_simulation.initial_order,
        events=first_simulation.events,
    )

    component_one = RetryScenario(
        simulation_id=first_simulation.id,
        target_sequence=1,
        retry_count=2,
    )
    component_two = RetryScenario(
        simulation_id=second_simulation.id,
        target_sequence=1,
        retry_count=2,
    )

    first = execute(first_simulation, component_one)
    second = execute(second_simulation, component_two)

    assert first.baseline == second.baseline
    assert first.adversarial_simulation == second.adversarial_simulation
    assert first.adversarial_result == second.adversarial_result
