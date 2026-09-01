from app.domain.models.adversarial_simulation import (
    AdversarialSimulation,
    OutOfOrderEventAttack,
)
from app.domain.models.payment_simulation import PaymentSimulation


class OutOfOrderEventInjector:
    """Inject deterministic out-of-order event delivery."""

    @staticmethod
    def inject(
        simulation: PaymentSimulation,
        source_sequence: int,
        target_sequence: int,
    ) -> AdversarialSimulation:
        if source_sequence < 0 or target_sequence < 0:
            raise ValueError("Event sequences cannot be negative.")

        event_count = len(simulation.events)

        if source_sequence >= event_count:
            raise IndexError(
                f"Source sequence {source_sequence} is outside the simulation."
            )

        if target_sequence >= event_count:
            raise IndexError(
                f"Target sequence {target_sequence} is outside the simulation."
            )

        if source_sequence == target_sequence:
            raise ValueError(
                "Source and target sequences must be different."
            )

        events = list(simulation.events)
        moved_event = events.pop(source_sequence)
        events.insert(target_sequence, moved_event)

        transformed_events = tuple(
            event.__class__(
                sequence=sequence,
                event=event.event,
                occurred_at=event.occurred_at,
                id=event.id,
            )
            for sequence, event in enumerate(events)
        )

        attack = OutOfOrderEventAttack(
            simulation_id=simulation.id,
            source_sequence=source_sequence,
            target_sequence=target_sequence,
        )

        adversarial_simulation = PaymentSimulation(
            seed=simulation.seed,
            initial_payment=simulation.initial_payment,
            initial_order=simulation.initial_order,
            events=transformed_events,
            id=simulation.id,
        )

        return AdversarialSimulation(
            source_simulation=simulation,
            attack=attack,
            simulation=adversarial_simulation,
        )
