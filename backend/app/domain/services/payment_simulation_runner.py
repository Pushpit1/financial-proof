import random
from collections.abc import Sequence
from datetime import datetime, timedelta

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

        payment = simulation.initial_payment
        order = simulation.initial_order

        trace: list[SimulationTraceEntry] = []
        snapshots: list[SimulationStateSnapshot] = []

        for event in simulation.events:
            payment_before = payment
            order_before = order

            payment = PaymentStateMachine.transition(payment, event.event)
            order = cls._transition_order(order, event.event)

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

        return SimulationResult(
            simulation_id=simulation.id,
            seed=simulation.seed,
            initial_payment=simulation.initial_payment,
            initial_order=simulation.initial_order,
            final_payment=payment,
            final_order=order,
            trace=tuple(trace),
            snapshots=tuple(snapshots),
        )

    @classmethod
    def replay(cls, simulation: PaymentSimulation) -> SimulationResult:
        """Replay the exact recorded simulation deterministically."""

        return cls.run(simulation)

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
