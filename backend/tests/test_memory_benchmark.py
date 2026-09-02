"""Tests for simulation memory benchmarking."""

from __future__ import annotations

import json

import pytest

from benchmarks.memory_benchmark import measure_memory


def test_memory_benchmark_is_reproducible_in_shape(
    tmp_path,
    monkeypatch,
) -> None:
    import benchmarks.memory_benchmark as module

    monkeypatch.setattr(module, "RESULTS_PATH", tmp_path)

    result = measure_memory(
        simulation_count=2,
        event_count=3,
        iterations=1,
    )

    assert result["workload"] == {
        "simulation_count": 2,
        "events_per_simulation": 3,
        "total_events": 6,
    }

    assert result["memory_bytes"]["average_peak"] > 0
    assert result["memory_megabytes"]["average_peak"] > 0


def test_memory_benchmark_writes_result_file(
    tmp_path,
    monkeypatch,
) -> None:
    import benchmarks.memory_benchmark as module

    monkeypatch.setattr(module, "RESULTS_PATH", tmp_path)

    measure_memory(
        simulation_count=2,
        event_count=3,
        iterations=1,
    )

    result_path = tmp_path / "memory_2_3.json"

    assert result_path.exists()

    payload = json.loads(
        result_path.read_text(encoding="utf-8"),
    )

    assert payload["benchmark"]["name"] == "payment_simulation_memory"


@pytest.mark.parametrize(
    ("simulation_count", "event_count", "iterations"),
    [
        (0, 3, 1),
        (1, 0, 1),
        (1, 3, 0),
    ],
)
def test_memory_benchmark_rejects_invalid_arguments(
    simulation_count: int,
    event_count: int,
    iterations: int,
) -> None:
    with pytest.raises(ValueError):
        measure_memory(
            simulation_count=simulation_count,
            event_count=event_count,
            iterations=iterations,
        )
