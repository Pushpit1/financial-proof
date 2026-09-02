"""Tests for reproducible payment simulation throughput benchmarks."""

from __future__ import annotations

import json

import pytest

from benchmarks.simulation_throughput import (
    VALID_EVENT_SEQUENCE,
    build_simulations,
    run_benchmark,
)


def _workload_signature(simulations) -> tuple:
    return tuple(
        (
            simulation.seed,
            simulation.initial_payment,
            simulation.initial_order,
            tuple(
                (
                    event.sequence,
                    event.event,
                    event.occurred_at,
                )
                for event in simulation.events
            ),
        )
        for simulation in simulations
    )


def test_build_simulations_is_deterministic() -> None:
    first = build_simulations(
        simulation_count=3,
        event_count=3,
    )
    second = build_simulations(
        simulation_count=3,
        event_count=3,
    )

    assert _workload_signature(first) == _workload_signature(second)


def test_build_simulations_uses_valid_event_prefix() -> None:
    simulations = build_simulations(
        simulation_count=2,
        event_count=3,
    )

    assert all(
        tuple(event.event for event in simulation.events)
        == VALID_EVENT_SEQUENCE
        for simulation in simulations
    )


def test_build_simulations_uses_distinct_seeds() -> None:
    simulations = build_simulations(
        simulation_count=3,
        event_count=3,
    )

    assert tuple(simulation.seed for simulation in simulations) == (0, 1, 2)


def test_benchmark_runs_real_simulation_batch(tmp_path, monkeypatch) -> None:
    import benchmarks.simulation_throughput as module

    monkeypatch.setattr(module, "RESULTS_PATH", tmp_path)

    payload = run_benchmark(
        simulation_count=3,
        event_count=3,
        warmups=0,
        iterations=2,
    )

    assert payload["workload"] == {
        "simulation_count": 3,
        "events_per_simulation": 3,
        "total_events": 9,
    }

    assert payload["benchmark"]["iterations"] == 2
    assert payload["derived"]["events_per_second"] > 0


def test_benchmark_result_file_is_written(tmp_path, monkeypatch) -> None:
    import benchmarks.simulation_throughput as module

    monkeypatch.setattr(module, "RESULTS_PATH", tmp_path)

    run_benchmark(
        simulation_count=2,
        event_count=3,
        warmups=0,
        iterations=1,
    )

    result_path = tmp_path / "simulation_2_3.json"

    assert result_path.exists()

    payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert payload["workload"]["total_events"] == 6
    assert payload["derived"]["events_per_second"] > 0


@pytest.mark.parametrize("event_count", [0, 4])
def test_build_simulations_rejects_invalid_event_count(
    event_count: int,
) -> None:
    with pytest.raises(ValueError):
        build_simulations(
            simulation_count=1,
            event_count=event_count,
        )


def test_build_simulations_rejects_invalid_simulation_count() -> None:
    with pytest.raises(ValueError):
        build_simulations(
            simulation_count=0,
            event_count=3,
        )
