"""Tests for deterministic demo state management."""

from __future__ import annotations

from app.demo.seed import build_demo_seed
from app.demo.state import DemoState, DemoStateManager


def test_demo_state_starts_clean() -> None:
    state = DemoState.create()

    assert state.seed == build_demo_seed()
    assert state.compiled_contract is None
    assert state.simulation is None
    assert state.violations == []
    assert state.step_results == {}


def test_demo_state_records_steps() -> None:
    state = DemoState.create()

    state.record_step("compile", {"version": 1})
    state.record_step("verify", {"violations": 0})

    assert state.step_results == {
        "compile": {"version": 1},
        "verify": {"violations": 0},
    }


def test_demo_state_reset_preserves_seed_and_clears_results() -> None:
    state = DemoState.create()
    state.compiled_contract = {"id": "contract"}
    state.verification_result = {"violations": 1}
    state.violations.append("refund-too-large")
    state.record_step("verify", {"violations": 1})

    original_seed = state.seed
    reset_state = state.reset()

    assert reset_state is state
    assert state.seed == original_seed
    assert state.compiled_contract is None
    assert state.verification_result is None
    assert state.violations == []
    assert state.step_results == {}


def test_demo_state_runtime_reset_preserves_seed() -> None:
    state = DemoState.create()
    state.compiled_contract = {"id": "contract"}
    state.simulation = {"id": "simulation"}
    state.record_step("compile", True)

    seed = state.seed
    state.clear_runtime_results()

    assert state.seed == seed
    assert state.compiled_contract is None
    assert state.simulation is None
    assert state.step_results == {}


def test_demo_state_manager_reset_is_deterministic() -> None:
    manager = DemoStateManager()

    first = manager.state
    first_snapshot = manager.snapshot()

    first.compiled_contract = {"id": "changed"}
    first.violations.append("violation")

    second = manager.reset()
    second_snapshot = manager.snapshot()

    assert second is manager.state
    assert second_snapshot == first_snapshot
    assert second.compiled_contract is None
    assert second.violations == []


def test_demo_state_manager_runtime_reset_keeps_seed_identity() -> None:
    manager = DemoStateManager()

    manager.state.compiled_contract = {"id": "contract"}
    manager.state.record_step("compile", True)

    seed = manager.state.seed
    reset_state = manager.reset_runtime()

    assert reset_state is manager.state
    assert reset_state.seed == seed
    assert reset_state.compiled_contract is None
    assert reset_state.step_results == {}


def test_demo_snapshot_exposes_progress_without_runtime_objects() -> None:
    manager = DemoStateManager()

    manager.state.record_step("compile", {"contract_id": "secret-runtime-object"})
    snapshot = manager.snapshot()

    assert snapshot["seed"] == 20260902
    assert snapshot["contract_id"]
    assert snapshot["payment_id"]
    assert snapshot["completed_steps"] == ["compile"]
    assert "secret-runtime-object" not in str(snapshot)
