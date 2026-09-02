"""Tests for the deterministic demo runner foundation."""

from app.demo.runner import DemoRunner
from app.demo.seed import build_demo_seed
from app.demo.state import DemoStateManager


def test_runner_uses_canonical_seed() -> None:
    runner = DemoRunner()

    assert runner.seed == build_demo_seed()
    assert runner.seed.seed == 20260902


def test_runner_exposes_eighteen_ordered_steps() -> None:
    runner = DemoRunner()

    assert len(runner.step_names()) == 18
    assert runner.step_names()[0] == "enter_business_rule"
    assert runner.step_names()[-1] == "generate_financial_proof"


def test_runner_records_successful_step() -> None:
    runner = DemoRunner()

    result = runner.mark_success(
        1,
        "Business rule accepted.",
        {"rule": runner.seed.business_rule},
    )

    assert result.number == 1
    assert result.name == "enter_business_rule"
    assert result.status == "success"
    assert runner.state.step_results[1] == result


def test_runner_rejects_wrong_step_name() -> None:
    runner = DemoRunner()

    try:
        runner.record_step(1, "compile_contract")
    except ValueError as exc:
        assert "enter_business_rule" in str(exc)
    else:
        raise AssertionError("Expected invalid step name to raise ValueError.")


def test_runner_reset_clears_runtime_state() -> None:
    manager = DemoStateManager()
    runner = DemoRunner(manager)

    runner.mark_success(1, "accepted")
    original_seed = runner.seed

    reset_state = runner.reset()

    assert reset_state.seed == original_seed
    assert reset_state.step_results == {}
    assert reset_state.compiled_contract is None


def test_runner_initial_context_is_deterministic() -> None:
    runner = DemoRunner()

    assert runner.build_initial_context() == {
        "seed": 20260902,
        "contract_id": str(runner.seed.contract_id),
        "contract_name": "customer-refund-safety",
        "contract_version": 1,
        "business_rule": (
            "A customer refund must never exceed the original payment amount."
        ),
        "order_id": str(runner.seed.order_id),
        "payment_id": str(runner.seed.payment_id),
        "simulation_id": str(runner.seed.simulation_id),
        "amount_minor": 5000,
        "currency": "INR",
    }


def test_replay_returns_clean_deterministic_state() -> None:
    runner = DemoRunner()

    runner.mark_success(1, "accepted")
    replayed = runner.replay()

    assert replayed.step_results == {}
    assert replayed.seed == build_demo_seed()
