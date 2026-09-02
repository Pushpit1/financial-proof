"""Reproducible benchmark harness primitives."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class BenchmarkResult:
    """Measured result for one benchmark workload."""

    name: str
    workload_size: int
    warmups: int
    iterations: int
    total_seconds: float
    average_seconds: float
    minimum_seconds: float
    maximum_seconds: float
    throughput_per_second: float

    def as_dict(self) -> dict[str, float | int | str]:
        """Return a deterministic serialization-friendly representation."""

        return {
            "name": self.name,
            "workload_size": self.workload_size,
            "warmups": self.warmups,
            "iterations": self.iterations,
            "total_seconds": self.total_seconds,
            "average_seconds": self.average_seconds,
            "minimum_seconds": self.minimum_seconds,
            "maximum_seconds": self.maximum_seconds,
            "throughput_per_second": self.throughput_per_second,
        }


def benchmark(
    name: str,
    workload_size: int,
    operation: Callable[[], T],
    *,
    warmups: int = 2,
    iterations: int = 10,
) -> tuple[BenchmarkResult, list[T]]:
    """Measure a deterministic operation without including warmups."""

    if not name.strip():
        raise ValueError("Benchmark name cannot be empty.")

    if workload_size < 1:
        raise ValueError("Workload size must be positive.")

    if warmups < 0:
        raise ValueError("Warmups cannot be negative.")

    if iterations < 1:
        raise ValueError("Iterations must be positive.")

    for _ in range(warmups):
        operation()

    durations: list[float] = []
    outputs: list[T] = []

    for _ in range(iterations):
        started_at = perf_counter()
        outputs.append(operation())
        durations.append(perf_counter() - started_at)

    total_seconds = sum(durations)
    average_seconds = total_seconds / iterations
    minimum_seconds = min(durations)
    maximum_seconds = max(durations)

    throughput_per_second = (
        workload_size * iterations / total_seconds
        if total_seconds > 0
        else float("inf")
    )

    return (
        BenchmarkResult(
            name=name,
            workload_size=workload_size,
            warmups=warmups,
            iterations=iterations,
            total_seconds=total_seconds,
            average_seconds=average_seconds,
            minimum_seconds=minimum_seconds,
            maximum_seconds=maximum_seconds,
            throughput_per_second=throughput_per_second,
        ),
        outputs,
    )
