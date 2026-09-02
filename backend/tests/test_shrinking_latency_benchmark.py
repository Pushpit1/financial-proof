"""Tests for counterexample shrinking latency benchmarks."""

from __future__ import annotations

import json

import pytest

from benchmarks.shrinking_latency import (
    build_simulation,
    run_benchmark,
)


def test_build_simulation_is_deterministic() -> None:
    first = build_simulation(5)
    second = build_simulation(5)

    assert first == second


def test_build_simulation_has_requested_event_count() -> None:
    simulation = build_simulation(7)

    assert len(simulation.events) == 7
    assert [event.sequence for event in simulation.events] == list(range(7))


def test_benchmark_produces_minimal_counterexample(
    tmp_path,
    monkeypatch,
) -> None:
    import benchmarks.shrinking_latency as module

    monkeypatch.setattr(module, "RESULTS_PATH", tmp_path)

    payload = run_benchmark(
        event_count=5,
        warmups=0,
        iterations=2,
    )

    assert payload["workload"]["event_count"] == 5
    assert payload["benchmark"]["iterations"] == 2
    assert payload["benchmark"]["throughput_per_second"] > 0
    assert payload["derived"]["microseconds_per_event"] > 0


def test_benchmark_writes_result_file(tmp_path, monkeypatch) -> None:
    import benchmarks.shrinking_latency as module

    monkeypatch.setattr(module, "RESULTS_PATH", tmp_path)

    run_benchmark(
        event_count=3,
        warmups=0,
        iterations=1,
    )

    result_path = tmp_path / "shrink_3.json"

    assert result_path.exists()

    payload = json.loads(
        result_path.read_text(encoding="utf-8"),
    )

    assert payload["workload"]["event_count"] == 3


def test_build_simulation_rejects_invalid_count() -> None:
    with pytest.raises(ValueError):
        build_simulation(0)
