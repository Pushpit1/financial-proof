from collections.abc import Callable

from app.domain.models.counterexample import Counterexample
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)


ViolationPredicate = Callable[[PaymentSimulation], bool]


class CounterexampleShrinkingMetrics:
    """Immutable metrics describing one deterministic shrink operation."""

    def __init__(
        self,
        *,
        original_event_count: int,
        minimized_event_count: int,
        candidate_count: int,
        reproduction_checks: int,
    ) -> None:
        self.original_event_count = original_event_count
        self.minimized_event_count = minimized_event_count
        self.candidate_count = candidate_count
        self.reproduction_checks = reproduction_checks

    @property
    def removed_event_count(self) -> int:
        return self.original_event_count - self.minimized_event_count

    @property
    def reduction_ratio(self) -> float:
        if self.original_event_count == 0:
            return 0.0

        return self.removed_event_count / self.original_event_count


class CounterexampleShrinkResult:
    """Immutable result containing a minimized counterexample and proof."""

    def __init__(
        self,
        *,
        counterexample: Counterexample,
        metrics: CounterexampleShrinkingMetrics,
        reproduces_violation: bool,
    ) -> None:
        self.counterexample = counterexample
        self.metrics = metrics
        self.reproduces_violation = reproduces_violation


class CounterexampleShrinker:
    """Deterministically shrink a payment counterexample."""

    @staticmethod
    def _without_event(
        simulation: PaymentSimulation,
        remove_sequence: int,
    ) -> PaymentSimulation:
        """Return a simulation with one event removed and sequences rebuilt."""

        remaining_events = [
            event
            for event in simulation.events
            if event.sequence != remove_sequence
        ]

        normalized_events = tuple(
            SimulationEvent(
                sequence=sequence,
                event=event.event,
                occurred_at=event.occurred_at,
                id=event.id,
            )
            for sequence, event in enumerate(remaining_events)
        )

        return PaymentSimulation(
            seed=simulation.seed,
            initial_payment=simulation.initial_payment,
            initial_order=simulation.initial_order,
            events=normalized_events,
            id=simulation.id,
        )

    @classmethod
    def shrink(
        cls,
        counterexample: Counterexample,
        violation_predicate: ViolationPredicate,
    ) -> Counterexample:
        """Return the smallest one-event-removal counterexample."""

        return cls.shrink_with_metrics(
            counterexample,
            violation_predicate,
        ).counterexample

    @classmethod
    def shrink_with_metrics(
        cls,
        counterexample: Counterexample,
        violation_predicate: ViolationPredicate,
    ) -> CounterexampleShrinkResult:
        """Shrink deterministically and prove the violation still reproduces."""

        reproduction_checks = 1

        if not violation_predicate(counterexample.simulation):
            raise ValueError(
                "Counterexample does not reproduce its violation."
            )

        original_event_count = counterexample.original_event_count
        current = counterexample.simulation
        candidate_count = 0
        sequence = 0

        while sequence < len(current.events):
            candidate = cls._without_event(current, sequence)
            candidate_count += 1
            reproduction_checks += 1

            if violation_predicate(candidate):
                current = candidate
            else:
                sequence += 1

        minimized = Counterexample(
            simulation_id=current.id,
            simulation=current,
            violation_code=counterexample.violation_code,
            original_event_count=original_event_count,
            minimized_event_count=len(current.events),
        )

        reproduces_violation = violation_predicate(minimized.simulation)
        reproduction_checks += 1

        metrics = CounterexampleShrinkingMetrics(
            original_event_count=original_event_count,
            minimized_event_count=len(current.events),
            candidate_count=candidate_count,
            reproduction_checks=reproduction_checks,
        )

        return CounterexampleShrinkResult(
            counterexample=minimized,
            metrics=metrics,
            reproduces_violation=reproduces_violation,
        )
