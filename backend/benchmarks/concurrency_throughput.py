"""Reproducible concurrency and idempotency throughput benchmarks."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.domain.models.idempotency import IdempotencyKey
from app.domain.services.idempotency import IdempotencyService
from app.domain.services.idempotent_execution import IdempotentExecutionService
from benchmarks.harness import benchmark

RESULTS_PATH = Path("benchmarks/results")


def _build_service() -> IdempotentExecutionService:
    """Create a fresh isolated idempotency execution service."""
    return IdempotentExecutionService(IdempotencyService())


def _run_same_key(
    *,
    worker_count: int,
    service: IdempotentExecutionService,
) -> list[object]:
    """Execute concurrent retries against one logical operation."""
    key = IdempotencyKey("concurrency-benchmark")
    fingerprint = "concurrency-response"

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [
            executor.submit(
                service.execute,
                key,
                fingerprint,
            )
            for _ in range(worker_count)
        ]

        return [future.result() for future in futures]


def _run_different_keys(
    *,
    worker_count: int,
    service: IdempotentExecutionService,
) -> list[object]:
    """Execute independent operations concurrently."""
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [
            executor.submit(
                service.execute,
                IdempotencyKey(f"concurrency-{index}"),
                f"response-{index}",
            )
            for index in range(worker_count)
        ]

        return [future.result() for future in futures]


def run_benchmark(
    *,
    worker_count: int,
    warmups: int = 2,
    iterations: int = 5,
) -> dict[str, object]:
    """Measure concurrent same-key and independent-key execution."""
    if worker_count < 1:
        raise ValueError("worker_count must be at least 1.")

    def operation() -> tuple[list[object], list[object]]:
        service = _build_service()

        same_key_results = _run_same_key(
            worker_count=worker_count,
            service=service,
        )

        independent_results = _run_different_keys(
            worker_count=worker_count,
            service=_build_service(),
        )

        return same_key_results, independent_results

    result, outputs = benchmark(
        name="idempotent_concurrency",
        workload_size=worker_count * 2,
        operation=operation,
        warmups=warmups,
        iterations=iterations,
    )

    same_key_executions = [
        sum(result.executed for result in output[0])
        for output in outputs
    ]
    independent_executions = [
        sum(result.executed for result in output[1])
        for output in outputs
    ]

    for count in same_key_executions:
        if count != 1:
            raise RuntimeError(
                "Concurrent same-key workload did not execute exactly once."
            )

    for count in independent_executions:
        if count != worker_count:
            raise RuntimeError(
                "Independent-key workload did not execute every operation."
            )

    payload = {
        "benchmark": result.as_dict(),
        "workload": {
            "worker_count": worker_count,
            "same_key_operations": worker_count,
            "independent_key_operations": worker_count,
            "total_operations_per_iteration": worker_count * 2,
        },
        "correctness": {
            "same_key_executions": same_key_executions,
            "independent_key_executions": independent_executions,
        },
    }

    RESULTS_PATH.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_PATH / (
        f"concurrency_{worker_count}.json"
    )
    output_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return payload


if __name__ == "__main__":
    for worker_count in (2, 10, 50, 100):
        payload = run_benchmark(
            worker_count=worker_count,
        )
        print(json.dumps(payload, indent=2))
