"""Tests for the deterministic demo lifecycle API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies.demo import get_demo_state_manager
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    get_demo_state_manager.cache_clear()


def test_demo_state_starts_deterministically() -> None:
    response = client.get("/demo/state")

    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    assert payload["state"]["seed"] == 20260902
    assert payload["state"]["violation_count"] == 0
    assert payload["state"]["completed_steps"] == []


def test_demo_reset_returns_clean_state() -> None:
    manager = get_demo_state_manager()
    manager.state.compiled_contract = {"changed": True}
    manager.state.violations.append("violation")
    manager.state.record_step("compile", True)

    response = client.post("/demo/reset")

    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    assert payload["state"]["has_compiled_contract"] is False
    assert payload["state"]["violation_count"] == 0
    assert payload["state"]["completed_steps"] == []


def test_demo_replay_returns_canonical_context() -> None:
    manager = get_demo_state_manager()
    manager.state.record_step("verify", {"violations": 1})

    response = client.post("/demo/replay")

    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    assert payload["seed"] == 20260902
    assert payload["event_count"] == 2
    assert payload["state"]["completed_steps"] == []
    assert payload["state"]["violation_count"] == 0


def test_demo_replay_is_deterministic() -> None:
    first = client.post("/demo/replay").json()
    second = client.post("/demo/replay").json()

    assert first["seed"] == second["seed"]
    assert first["simulation_id"] == second["simulation_id"]
    assert first["state"] == second["state"]
