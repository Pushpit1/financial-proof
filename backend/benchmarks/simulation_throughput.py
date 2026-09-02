"""Reproducible payment simulation throughput benchmarks."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import PaymentSimulation, SimulationEvent
from app.domain.services.payment_simulation_batch_runner import (
    PaymentSimulationBatchRunner,
)
from benchmarks.harness import benchmark

RESULTS_PATH = Path("benchmarks/results")

BENCHMARK_PAYMENT_ID = UUID("00000000-0000-0000-0000-000000000001")
BENCHMARK_ORDER_ID = UUID("00000000-0000-0000-0000-000000000002")
BENCHMARK_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

VALID_EVENT_SEQUENCE = (
    PaymentEvent.AUTHORIZE,
    PaymentEvent.CAPTURE,
    PaymentEvent.REFUND,
)


def _build_events(event_count: int) -> tuple[SimulationEvent, ...]:
    """Build the exact valid event prefix used by the benchmark."""
    if not 1 <= event_count <= len(VALID_EVENT_SEQUENCE):
        raise ValueError(
            "event_count must be between 1 and "
            f"{len(VALID_EVENT_SEQUENCE)}."
        )

    return tuple(
        SimulationEvent(
            sequence=sequence,
            event=event,
            occurred_at=BENCHMARK_CREATED_AT + timedelta(seconds=sequence),
        )
        for sequence, event in enumerate(
            VALID_EVENT_SEQUENCE[:event_count]
        )
    )


def build_simulations(
    *,
    simulation_count: int,
    event_count: int,
) -> tuple[PaymentSimulation, ...]:
    """Build deterministic simulations with valid state-machine events."""
    if simulation_count < 1:
        raise ValueError("simulation_count must be at least 1.")

    events = _build_events(event_count)

    payment = Payment(
        order_id=str(BENCHMARK_ORDER_ID),
        amount_minor=1000,
        currency="INR",
        id=BENCHMARK_PAYMENT_ID,
        created_at=BENCHMARK_CREATED_AT,
    )

    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
        id=BENCHMARK_ORDER_ID,
        created_at=BENCHMARK_CREATED_AT,
    )

    return tuple(
        PaymentSimulation(
            seed=seed,
            initial_payment=payment,
            initial_order=order,
            events=events,
        )
        for seed in range(simulation_count)
    )


def run_benchmark(
    *,
    simulation_count: int,
    event_count: int,
    warmups: int = 2,
    iterations: int = 5,
) -> dict[str, object]:
    """Run and persist a reproducible payment simulation benchmark."""
    simulations = build_simulations(
        simulation_count=simulation_count,
        event_count=event_count,
    )

    workload_size = simulation_count * event_count

    result, outputs = benchmark(
        name="payment_simulation_batch",
        workload_size=workload_size,
        operation=lambda: PaymentSimulationBatchRunner.run(simulations),
        warmups=warmups,
        iterations=iterations,
    )

    for output in outputs:
        if len(output) != simulation_count:
            raise RuntimeError(
                "Simulation batch returned an unexpected number of results."
            )

    events_per_second = (
        workload_size / result.average_seconds
        if result.average_seconds > 0
        else 0.0
    )

    payload = {
        "benchmark": result.as_dict(),
        "workload": {
            "simulation_count": simulation_count,
            "events_per_simulation": event_count,
            "total_events": workload_size,
        },
        "derived": {
            "events_per_second": events_per_second,
        },
    }

    RESULTS_PATH.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_PATH / (
        f"simulation_{simulation_count}_{event_count}.json"
    )
    output_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return payload


if __name__ == "__main__":
    payload = run_benchmark(
        simulation_count=1000,
        event_count=3,
    )
    print(json.dumps(payload, indent=2))
