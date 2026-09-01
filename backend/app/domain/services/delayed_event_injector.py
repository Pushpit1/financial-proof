from app.domain.models.adversarial_simulation import (
    AdversarialSimulation,
    DelayedEventAttack,
)
from app.domain.models.payment_simulation import PaymentSimulation


class DelayedEventInjector:
    """Inject deterministic delayed event delivery."""

    @staticmethod
    def inject(
        simulation: PaymentSimulation,
        target_sequence: int,
        delay_seconds: int,
    ) -> AdversarialSimulation:
        if target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")

        if delay_seconds <= 0:
            raise ValueError("Delivery delay must be positive.")

        if target_sequence >= len(simulation.events):
            raise IndexError(
                f"Target sequence {target_sequence} is outside the simulation."
            )

        events = list(simulation.events)
        delayed_event = events.pop(target_sequence)
        insertion_sequence = min(
            target_sequence + 1,
            len(events),
        )
        events.insert(insertion_sequence, delayed_event)

        transformed_events = tuple(
            event.__class__(
                sequence=sequence,
                event=event.event,
                occurred_at=event.occurred_at,
                id=event.id,
            )
            for sequence, event in enumerate(events)
        )

        attack = DelayedEventAttack(
            simulation_id=simulation.id,
            target_sequence=target_sequence,
            delivery_delay_seconds=delay_seconds,
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
