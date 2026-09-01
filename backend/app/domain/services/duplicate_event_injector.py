from app.domain.models.adversarial_simulation import (
    AdversarialSimulation,
    DuplicateEventAttack,
)
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)


class DuplicateEventInjector:
    """Inject deterministic duplicate deliveries into payment simulations."""

    @staticmethod
    def inject(
        simulation: PaymentSimulation,
        target_sequence: int,
    ) -> AdversarialSimulation:
        if target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")

        if target_sequence >= len(simulation.events):
            raise IndexError(
                f"Target sequence {target_sequence} is outside the simulation."
            )

        target = simulation.events[target_sequence]

        duplicated = SimulationEvent(
            sequence=target_sequence + 1,
            event=target.event,
            occurred_at=target.occurred_at,
        )

        transformed_events = tuple(
            event if event.sequence <= target_sequence else SimulationEvent(
                sequence=event.sequence + 1,
                event=event.event,
                occurred_at=event.occurred_at,
                id=event.id,
            )
            for event in simulation.events
        )

        transformed_events = (
            transformed_events[: target_sequence + 1]
            + (duplicated,)
            + transformed_events[target_sequence + 1 :]
        )

        adversarial_simulation = PaymentSimulation(
            seed=simulation.seed,
            initial_payment=simulation.initial_payment,
            initial_order=simulation.initial_order,
            events=transformed_events,
            id=simulation.id,
        )

        attack = DuplicateEventAttack(
            simulation_id=simulation.id,
            target_sequence=target_sequence,
        )

        return AdversarialSimulation(
            source_simulation=simulation,
            attack=attack,
            simulation=adversarial_simulation,
        )
