"""Reproducible memory benchmarks for payment simulation execution."""

from __future__ import annotations

import gc
import json
import tracemalloc
from pathlib import Path

from app.domain.services.payment_simulation_batch_runner import (
    PaymentSimulationBatchRunner,
)
from benchmarks.simulation_throughput import build_simulations

RESULTS_PATH = Path("benchmarks/results")


def measure_memory(
    *,
    simulation_count: int,
    event_count: int,
    iterations: int = 3,
) -> dict[str, object]:
    """Measure current and peak traced memory for simulation execution."""
    if simulation_count < 1:
        raise ValueError("simulation_count must be at least 1.")

    if event_count < 1:
        raise ValueError("event_count must be at least 1.")

    if iterations < 1:
        raise ValueError("iterations must be at least 1.")

    simulations = build_simulations(
        simulation_count=simulation_count,
        event_count=event_count,
    )

    workload_size = simulation_count * event_count
    peaks: list[int] = []
    currents: list[int] = []

    for _ in range(iterations):
        gc.collect()
        tracemalloc.start()

        PaymentSimulationBatchRunner.run(simulations)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        currents.append(current)
        peaks.append(peak)

    payload = {
        "benchmark": {
            "name": "payment_simulation_memory",
            "iterations": iterations,
        },
        "workload": {
            "simulation_count": simulation_count,
            "events_per_simulation": event_count,
            "total_events": workload_size,
        },
        "memory_bytes": {
            "average_current": sum(currents) / len(currents),
            "minimum_current": min(currents),
            "maximum_current": max(currents),
            "average_peak": sum(peaks) / len(peaks),
            "minimum_peak": min(peaks),
            "maximum_peak": max(peaks),
        },
        "memory_megabytes": {
            "average_current": (
                sum(currents) / len(currents) / (1024 * 1024)
            ),
            "average_peak": (
                sum(peaks) / len(peaks) / (1024 * 1024)
            ),
            "maximum_peak": max(peaks) / (1024 * 1024),
        },
    }

    RESULTS_PATH.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_PATH / (
        f"memory_{simulation_count}_{event_count}.json"
    )
    output_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return payload


if __name__ == "__main__":
    payload = measure_memory(
        simulation_count=1000,
        event_count=3,
    )
    print(json.dumps(payload, indent=2))
