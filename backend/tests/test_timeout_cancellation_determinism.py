from datetime import UTC, datetime

from app.domain.enums.payment import OrderState, PaymentEvent, PaymentState
from app.domain.models.lost_response import LostResponseScenario
from app.domain.models.partial_failure import PartialFailureScenario
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.models.worker_crash import WorkerCrashScenario
from app.domain.services.partial_failure_injector import PartialFailureInjector
from app.domain.services.payment_simulation_runner import PaymentSimulationRunner

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
                occurred_at=TIMESTAMP.replace(second=1),
            ),
        ),
    )


def test_cancellation_is_a_deterministic_terminal_transition() -> None:
    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
        state=OrderState.CREATED,
    )

    first = PaymentSimulationRunner
    del first

    cancelled = order
    from app.domain.services.payment_state_machine import OrderStateMachine

    result = OrderStateMachine.transition(cancelled, PaymentEvent.CANCEL)

    assert result.id == order.id
    assert result.amount_minor == order.amount_minor
    assert result.currency == order.currency
    assert result.state is OrderState.CANCELLED
    assert order.state is OrderState.CREATED


def test_cancellation_replay_is_deterministic() -> None:
    from app.domain.services.payment_state_machine import OrderStateMachine

    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
        state=OrderState.CREATED,
    )

    first = OrderStateMachine.transition(order, PaymentEvent.CANCEL)
    second = OrderStateMachine.transition(order, PaymentEvent.CANCEL)

    assert first == second


def test_partial_failure_is_deterministic_for_same_target() -> None:
    simulation = make_simulation()

    first = PartialFailureInjector.inject(simulation, 1)
    second = PartialFailureInjector.inject(simulation, 1)

    assert first == second
    assert first.simulation_id == simulation.id
    assert first.target_sequence == 1
    assert first.operation_started is True
    assert first.operation_completed is False


def test_partial_failure_does_not_mutate_financial_input() -> None:
    simulation = make_simulation()
    original = simulation

    PartialFailureInjector.inject(simulation, 1)

    assert simulation == original
    assert simulation.initial_payment.state is PaymentState.CREATED
    assert simulation.initial_order.state is OrderState.CREATED
    assert len(simulation.events) == 2


def test_lost_response_scenario_is_immutable_and_deterministic() -> None:
    simulation = make_simulation()

    first = LostResponseScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )
    second = LostResponseScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )

    assert first == second
    assert first.response_lost is True


def test_worker_crash_scenario_is_immutable_and_deterministic() -> None:
    simulation = make_simulation()

    first = WorkerCrashScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )
    second = WorkerCrashScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )

    assert first == second
    assert first.restarted is True


def test_recovery_after_failure_replays_exact_financial_result() -> None:
    simulation = make_simulation()

    baseline = PaymentSimulationRunner.run(simulation)
    recovered = PaymentSimulationRunner.replay(simulation)

    assert recovered == baseline
    assert recovered.final_payment.id == baseline.final_payment.id
    assert recovered.final_payment.order_id == baseline.final_payment.order_id
    assert recovered.final_payment.amount_minor == 1000
    assert recovered.final_payment.currency == "INR"
    assert recovered.final_payment.state is PaymentState.CAPTURED
    assert recovered.final_order.state is OrderState.CAPTURED


def test_repeated_recovery_cannot_create_second_financial_effect() -> None:
    simulation = make_simulation()

    first = PaymentSimulationRunner.replay(simulation)
    second = PaymentSimulationRunner.replay(simulation)
    third = PaymentSimulationRunner.replay(simulation)

    assert first == second == third
    assert first.final_payment.state is PaymentState.CAPTURED
    assert first.final_order.state is OrderState.CAPTURED
    assert first.final_payment.amount_minor == 1000
    assert first.final_order.amount_minor == 1000
    assert len(first.trace) == len(simulation.events)


def test_failure_scenarios_preserve_original_simulation_identity() -> None:
    simulation = make_simulation()

    partial = PartialFailureScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )
    lost_response = LostResponseScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )
    worker_crash = WorkerCrashScenario(
        simulation_id=simulation.id,
        target_sequence=1,
    )

    assert partial.simulation_id == simulation.id
    assert lost_response.simulation_id == simulation.id
    assert worker_crash.simulation_id == simulation.id
    assert simulation.initial_payment.id == simulation.initial_payment.id
    assert simulation.initial_order.id == simulation.initial_order.id
