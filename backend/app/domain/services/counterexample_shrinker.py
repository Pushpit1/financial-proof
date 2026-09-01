import structlog

from app.core.metrics import get_metrics_registry
from app.core.observability import bind_observability_context
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)

logger = structlog.get_logger(__name__)


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
        reproduces_failure,
    ) -> PaymentSimulation:
        """Return the shortest event prefix that still reproduces failure."""

        simulation_id = str(simulation.id)

        bind_observability_context(
            simulation_id=simulation_id,
        )

        logger.info(
            "counterexample_shrink_started",
            simulation_id=simulation_id,
            original_event_count=len(simulation.events),
        )

        if not reproduces_failure(simulation):
            get_metrics_registry().counter(
                "counterexample_shrink_rejections_total",
            ).increment()

            logger.info(
                "counterexample_shrink_rejected",
                simulation_id=simulation_id,
                reason="input_does_not_reproduce_failure",
            )

            raise ValueError(
                "Counterexample shrinker requires an input that reproduces "
                "the failure."
            )

        get_metrics_registry().counter(
            "counterexample_shrinks_total",
        ).increment()

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

        logger.info(
            "counterexample_shrink_completed",
            simulation_id=simulation_id,
            original_event_count=len(simulation.events),
            minimized_event_count=len(current.events),
        )

        return current
