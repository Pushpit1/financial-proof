"""Reproducible counterexample shrinking latency benchmarks."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from app.domain.enums.payment import PaymentEvent, PaymentState
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)
from app.domain.services.counterexample_shrinker import CounterexampleShrinker
from benchmarks.harness import benchmark

RESULTS_PATH = Path("benchmarks/results")

EVENT_SEQUENCE = (
    PaymentEvent.AUTHORIZE,
    PaymentEvent.CAPTURE,
    PaymentEvent.REFUND,
)

ORDER_ID = UUID("00000000-0000-0000-0000-000000000042")
PAYMENT_ID = UUID("00000000-0000-0000-0000-000000000043")
SIMULATION_ID = UUID("00000000-0000-0000-0000-000000000044")

BASE_TIMESTAMP = datetime(2026, 8, 31, tzinfo=UTC)


def build_simulation(event_count: int) -> PaymentSimulation:
    """Build a deterministic simulation with the requested event count."""
    if event_count < 1:
        raise ValueError("event_count must be at least 1.")

    order = PaymentOrder(
        amount_minor=1000,
        currency="INR",
        id=ORDER_ID,
        created_at=BASE_TIMESTAMP,
    )

    payment = Payment(
        order_id=order.id,
        amount_minor=1000,
        currency="INR",
        state=PaymentState.CREATED,
        id=PAYMENT_ID,
        created_at=BASE_TIMESTAMP,
    )

    events = tuple(
        SimulationEvent(
            sequence=sequence,
            event=EVENT_SEQUENCE[sequence % len(EVENT_SEQUENCE)],
            occurred_at=BASE_TIMESTAMP + timedelta(seconds=sequence),
            id=UUID(
                f"00000000-0000-0000-0000-{sequence + 100:012d}"
            ),
        )
        for sequence in range(event_count)
    )

    return PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=events,
        id=SIMULATION_ID,
    )


def run_benchmark(
    *,
    event_count: int,
    warmups: int = 2,
    iterations: int = 5,
) -> dict[str, object]:
    """Measure latency for shrinking a failing simulation."""
    simulation = build_simulation(event_count)

    def operation() -> PaymentSimulation:
        return CounterexampleShrinker.shrink(
            simulation,
            lambda candidate: len(candidate.events) >= 1,
        )

    result, outputs = benchmark(
        name="counterexample_shrink",
        workload_size=event_count,
        operation=operation,
        warmups=warmups,
        iterations=iterations,
    )

    for output in outputs:
        if len(output.events) != 1:
            raise RuntimeError(
                "Shrinker did not produce the expected minimal result."
            )

    payload = {
        "benchmark": result.as_dict(),
        "workload": {
            "event_count": event_count,
        },
        "derived": {
            "microseconds_per_event": (
                result.average_seconds / event_count * 1_000_000
            ),
        },
    }

    RESULTS_PATH.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_PATH / f"shrink_{event_count}.json"
    output_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return payload


if __name__ == "__main__":
    payload = run_benchmark(
        event_count=100,
    )
    print(json.dumps(payload, indent=2))
