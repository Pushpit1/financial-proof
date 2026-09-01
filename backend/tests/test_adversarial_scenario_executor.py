from datetime import UTC, datetime

import pytest

from app.domain.enums.payment import PaymentEvent
from app.domain.models.adversarial_scenario import AdversarialScenario
from app.domain.models.adversarial_simulation import DuplicateEventAttack
from app.domain.models.lost_response import LostResponseScenario
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.services.adversarial_scenario_executor import (
    AdversarialScenarioExecutor,
)


def make_simulation() -> PaymentSimulation:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )
    payment = Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
    )

    return PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=(
            SimulationEvent(
                sequence=0,
                event=PaymentEvent.AUTHORIZE,
                occurred_at=datetime(2026, 8, 31, tzinfo=UTC),
            ),
        ),
    )


def test_executor_runs_baseline_simulation() -> None:
    simulation = make_simulation()

    scenario = AdversarialScenario(
        simulation_id=simulation.id,
        components=(),
    )

    result = AdversarialScenarioExecutor.execute(simulation, scenario)

    assert result.simulation_id == simulation.id
    assert result.baseline.simulation_id == simulation.id
    assert result.baseline.final_payment.state.value == "authorized"
    assert result.applied_components == ()


def test_executor_records_applied_components() -> None:
    simulation = make_simulation()

    scenario = AdversarialScenario(
        simulation_id=simulation.id,
        components=(
            DuplicateEventAttack(
                simulation_id=simulation.id,
                target_sequence=0,
            ),
        ),
    )

    result = AdversarialScenarioExecutor.execute(simulation, scenario)

    assert result.applied_components == (
        "DuplicateEventAttack",
    )


def test_executor_rejects_wrong_simulation() -> None:
    simulation = make_simulation()

    other = make_simulation()

    scenario = AdversarialScenario(
        simulation_id=other.id,
        components=(),
    )

    with pytest.raises(ValueError, match="different simulation"):
        AdversarialScenarioExecutor.execute(simulation, scenario)


def test_executor_rejects_invalid_target() -> None:
    simulation = make_simulation()

    scenario = AdversarialScenario(
        simulation_id=simulation.id,
        components=(
            DuplicateEventAttack(
                simulation_id=simulation.id,
                target_sequence=99,
            ),
        ),
    )

    with pytest.raises(ValueError, match="nonexistent sequence"):
        AdversarialScenarioExecutor.execute(simulation, scenario)


def test_executor_describes_effect_for_multiple_component_types() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )
    payment = Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
    )

    simulation = PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=(
            SimulationEvent(
                sequence=0,
                event=PaymentEvent.AUTHORIZE,
                occurred_at=datetime(2026, 8, 31, tzinfo=UTC),
            ),
            SimulationEvent(
                sequence=1,
                event=PaymentEvent.CAPTURE,
                occurred_at=datetime(2026, 8, 31, 0, 1, tzinfo=UTC),
            ),
        ),
    )

    scenario = AdversarialScenario(
        simulation_id=simulation.id,
        components=(
            DuplicateEventAttack(
                simulation_id=simulation.id,
                target_sequence=0,
            ),
            LostResponseScenario(
                simulation_id=simulation.id,
                target_sequence=1,
            ),
        ),
    )

    result = AdversarialScenarioExecutor.execute(simulation, scenario)

    assert result.applied_components == (
        "DuplicateEventAttack",
        "LostResponseScenario",
    )
    assert result.attack_count == 2
    assert result.outcomes[0].target_sequence == 0
    assert result.outcomes[1].target_sequence == 1

def test_executor_marks_each_component_as_applied() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
    )
    payment = Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
    )

    simulation = PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=(
            SimulationEvent(
                sequence=0,
                event=PaymentEvent.AUTHORIZE,
                occurred_at=datetime(2026, 8, 31, tzinfo=UTC),
            ),
            SimulationEvent(
                sequence=1,
                event=PaymentEvent.CAPTURE,
                occurred_at=datetime(2026, 8, 31, 0, 1, tzinfo=UTC),
            ),
        ),
    )

    scenario = AdversarialScenario(
        simulation_id=simulation.id,
        components=(
            DuplicateEventAttack(
                simulation_id=simulation.id,
                target_sequence=0,
            ),
            LostResponseScenario(
                simulation_id=simulation.id,
                target_sequence=1,
            ),
        ),
    )

    result = AdversarialScenarioExecutor.execute(simulation, scenario)

    assert len(result.outcomes) == 2

    assert result.outcomes[0].component_type == "DuplicateEventAttack"
    assert result.outcomes[0].target_sequence == 0
    assert result.outcomes[0].status == "applied"

    assert result.outcomes[1].component_type == "LostResponseScenario"
    assert result.outcomes[1].target_sequence == 1
    assert result.outcomes[1].status == "applied"

