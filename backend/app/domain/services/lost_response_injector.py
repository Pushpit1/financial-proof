from app.domain.models.lost_response import LostResponseScenario
from app.domain.models.payment_simulation import PaymentSimulation


class LostResponseInjector:
    """Inject deterministic lost-response behavior."""

    @staticmethod
    def inject(
        simulation: PaymentSimulation,
        target_sequence: int,
    ) -> LostResponseScenario:
        if target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")

        if target_sequence >= len(simulation.events):
            raise IndexError(
                f"Target sequence {target_sequence} is outside the simulation."
            )

        return LostResponseScenario(
            simulation_id=simulation.id,
            target_sequence=target_sequence,
        )
