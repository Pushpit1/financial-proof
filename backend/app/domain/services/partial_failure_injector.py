from app.domain.models.partial_failure import PartialFailureScenario
from app.domain.models.payment_simulation import PaymentSimulation


class PartialFailureInjector:
    """Inject deterministic mid-operation failure."""

    @staticmethod
    def inject(
        simulation: PaymentSimulation,
        target_sequence: int,
    ) -> PartialFailureScenario:
        if target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")

        if target_sequence >= len(simulation.events):
            raise IndexError(
                f"Target sequence {target_sequence} is outside the simulation."
            )

        return PartialFailureScenario(
            simulation_id=simulation.id,
            target_sequence=target_sequence,
        )
