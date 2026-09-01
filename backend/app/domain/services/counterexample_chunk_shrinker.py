from collections.abc import Callable

from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)
from app.domain.services.counterexample_shrinker import (
    CounterexampleShrinker,
)


class CounterexampleChunkShrinker:
    """Deterministically remove contiguous event chunks from a counterexample."""

    @classmethod
    def _with_events(
        cls,
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
        """Remove deterministic contiguous chunks while failure survives."""
        if not reproduces_failure(simulation):
            raise ValueError(
                "Counterexample chunk shrinker requires an input that "
                "reproduces the failure."
            )

        current = CounterexampleShrinker.shrink(
            simulation,
            reproduces_failure,
        )

        chunk_size = max(1, len(current.events) // 2)

        while chunk_size > 0:
            changed = False

            for start in range(0, len(current.events) - chunk_size + 1):
                end = start + chunk_size

                candidate_events = (
                    current.events[:start] + current.events[end:]
                )

                candidate = cls._with_events(
                    current,
                    candidate_events,
                )

                if reproduces_failure(candidate):
                    current = candidate
                    changed = True
                    break

            if not changed:
                if chunk_size == 1:
                    break
                chunk_size //= 2

        return current
