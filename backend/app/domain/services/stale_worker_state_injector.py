from app.domain.models.payment_simulation import PaymentSimulation
from app.domain.models.stale_worker_state import StaleWorkerStateAttack


class StaleWorkerStateInjector:
    """Create deterministic stale-worker-state attack scenarios."""

    @staticmethod
    def inject(
        simulation: PaymentSimulation,
        worker_sequence: int,
        incoming_sequence: int,
    ) -> StaleWorkerStateAttack:
        if worker_sequence < 0:
            raise ValueError("Worker sequence cannot be negative.")

        if incoming_sequence < 0:
            raise ValueError("Incoming sequence cannot be negative.")

        if incoming_sequence >= len(simulation.events):
            raise IndexError(
                f"Incoming sequence {incoming_sequence} is outside the simulation."
            )

        return StaleWorkerStateAttack(
            simulation_id=simulation.id,
            worker_sequence=worker_sequence,
            incoming_sequence=incoming_sequence,
        )
