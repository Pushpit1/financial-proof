import random
from collections.abc import Sequence
from datetime import datetime, timedelta

import structlog

from app.core.logging import log_event
from app.core.metrics import get_metrics_registry
from app.core.observability import (
    bind_observability_context,
    clear_observability_context,
)
from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
    SimulationResult,
    SimulationStateSnapshot,
    SimulationTraceEntry,
)
from app.domain.services.deterministic_clock import DeterministicClock
from app.domain.services.payment_state_machine import (
    OrderStateMachine,
    PaymentStateMachine,
)

logger = structlog.get_logger(__name__)


class PaymentSimulationRunner:
    """Execute payment simulations deterministically."""

    @staticmethod
    def create_events(
        seed: int,
        event_count: int,
        start_time: datetime,
        step: timedelta = timedelta(seconds=1),
        allowed_events: Sequence[PaymentEvent] | None = None,
    ) -> tuple[SimulationEvent, ...]:
        """Create a reproducible sequence of simulation events."""

        if event_count < 0:
            raise ValueError("Event count cannot be negative.")

        events = tuple(
            allowed_events
            or (
                PaymentEvent.AUTHORIZE,
                PaymentEvent.CAPTURE,
                PaymentEvent.REFUND,
                PaymentEvent.FAIL,
            )
        )

        if not events and event_count:
            raise ValueError("At least one event must be available.")

        rng = random.Random(seed)
        clock = DeterministicClock(start_time, step)

        generated: list[SimulationEvent] = []

        for sequence in range(event_count):
            generated.append(
                SimulationEvent(
                    sequence=sequence,
                    event=rng.choice(events),
                    occurred_at=clock.now(),
                )
            )

            clock.advance()

        return tuple(generated)

    @staticmethod
    def _transition_order(order, event: PaymentEvent):
        """Apply an event to the order when the order owns that transition."""

        if event == PaymentEvent.REFUND:
            return order

        return OrderStateMachine.transition(order, event)

    @classmethod
    def run(cls, simulation: PaymentSimulation) -> SimulationResult:
        """Execute every event in its exact recorded order."""

        simulation_id = str(simulation.id)

        bind_observability_context(
            simulation_id=simulation_id,
        )

        log_event(
            logger,
            "simulation_started",
            fields={
                "simulation_id": simulation_id,
                "seed": simulation.seed,
                "event_count": len(simulation.events),
            },
        )

        try:
            payment = simulation.initial_payment
            order = simulation.initial_order

            trace: list[SimulationTraceEntry] = []
            snapshots: list[SimulationStateSnapshot] = []

            for event in simulation.events:
                payment_before = payment
                order_before = order

                payment = PaymentStateMachine.transition(
                    payment,
                    event.event,
                )
                order = cls._transition_order(
                    order,
                    event.event,
                )

                trace.append(
                    SimulationTraceEntry(
                        sequence=event.sequence,
                        event=event.event,
                        occurred_at=event.occurred_at,
                        payment_before=payment_before,
                        payment_after=payment,
                        order_before=order_before,
                        order_after=order,
                    )
                )

                snapshots.append(
                    SimulationStateSnapshot(
                        sequence=event.sequence,
                        occurred_at=event.occurred_at,
                        payment=payment,
                        order=order,
                    )
                )

            get_metrics_registry().counter(
                "simulation_runs_total",
            ).increment()

            result = SimulationResult(
                simulation_id=simulation.id,
                seed=simulation.seed,
                initial_payment=simulation.initial_payment,
                initial_order=simulation.initial_order,
                final_payment=payment,
                final_order=order,
                trace=tuple(trace),
                snapshots=tuple(snapshots),
            )

            log_event(
                logger,
                "simulation_completed",
                fields={
                    "simulation_id": simulation_id,
                    "seed": simulation.seed,
                    "event_count": len(simulation.events),
                    "trace_count": len(result.trace),
                    "snapshot_count": len(result.snapshots),
                    "final_payment_state": result.final_payment.state.value,
                    "final_order_state": result.final_order.state.value,
                },
            )

            return result
        finally:
            clear_observability_context()

    @classmethod
    def replay(cls, simulation: PaymentSimulation) -> SimulationResult:
        """Replay the exact recorded simulation deterministically."""

        result = cls.run(simulation)

        log_event(
            logger,
            "simulation_replayed",
            fields={
                "simulation_id": str(simulation.id),
                "seed": simulation.seed,
                "event_count": len(simulation.events),
            },
        )

        return result

    @classmethod
    def replay_matches(
        cls,
        simulation: PaymentSimulation,
        expected: SimulationResult,
    ) -> bool:
        """Verify that replay produces the same deterministic result."""

        replayed = cls.replay(simulation)

        return (
            replayed.simulation_id == expected.simulation_id
            and replayed.seed == expected.seed
            and replayed.final_payment == expected.final_payment
            and replayed.final_order == expected.final_order
            and replayed.trace == expected.trace
            and replayed.snapshots == expected.snapshots
        )
