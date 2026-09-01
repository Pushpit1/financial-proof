import structlog

from app.core.metrics import get_metrics_registry
from app.core.observability import bind_observability_context
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)
from app.domain.services.counterexample_shrinker import (
    CounterexampleShrinker,
)

logger = structlog.get_logger(__name__)


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
        reproduces_failure,
    ) -> PaymentSimulation:
        """Remove deterministic contiguous chunks while failure survives."""

        simulation_id = str(simulation.id)

        bind_observability_context(
            simulation_id=simulation_id,
        )

        logger.info(
            "counterexample_chunk_shrink_started",
            simulation_id=simulation_id,
            original_event_count=len(simulation.events),
        )

        if not reproduces_failure(simulation):
            get_metrics_registry().counter(
                "counterexample_chunk_shrink_rejections_total",
            ).increment()

            logger.info(
                "counterexample_chunk_shrink_rejected",
                simulation_id=simulation_id,
                reason="input_does_not_reproduce_failure",
            )

            raise ValueError(
                "Counterexample chunk shrinker requires an input that "
                "reproduces the failure."
            )

        get_metrics_registry().counter(
            "counterexample_chunk_shrinks_total",
        ).increment()

        current = CounterexampleShrinker.shrink(
            simulation,
            reproduces_failure,
        )

        chunk_size = max(1, len(current.events) // 2)

        while chunk_size > 0:
            changed = False

            for start in range(
                0,
                len(current.events) - chunk_size + 1,
            ):
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

        logger.info(
            "counterexample_chunk_shrink_completed",
            simulation_id=simulation_id,
            original_event_count=len(simulation.events),
            minimized_event_count=len(current.events),
        )

        return current
