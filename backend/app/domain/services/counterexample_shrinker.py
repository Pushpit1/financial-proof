from collections.abc import Callable

from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)


class CounterexampleShrinker:
    """Deterministically minimize a failing payment simulation."""

    @staticmethod
    def _with_events(
        simulation: PaymentSimulation,
        events: tuple[SimulationEvent, ...],
    ) -> PaymentSimulation:
        normalized = tuple(
            SimulationEvent(
                sequence=sequence,
                event=event.event,
                occurred_at=event.occurred_at,
                id=event.id,
            )
            for sequence, event in enumerate(events)
        )

        return PaymentSimulation(
            seed=simulation.seed,
            initial_payment=simulation.initial_payment,
            initial_order=simulation.initial_order,
            events=normalized,
            id=simulation.id,
        )

    @classmethod
    def shrink(
        cls,
        simulation: PaymentSimulation,
        reproduces_failure: Callable[[PaymentSimulation], bool],
    ) -> PaymentSimulation:
        """Return the shortest event prefix that still reproduces failure."""
        if not reproduces_failure(simulation):
            raise ValueError(
                "Counterexample shrinker requires an input that reproduces "
                "the failure."
            )

        current = simulation

        while current.events:
            candidate_events = current.events[:-1]

            candidate = cls._with_events(
                current,
                candidate_events,
            )

            if not reproduces_failure(candidate):
                break

            current = candidate

        return current
