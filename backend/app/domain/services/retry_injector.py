from app.domain.models.payment_simulation import PaymentSimulation
from app.domain.models.retry import RetryScenario


class RetryInjector:
    """Inject deterministic request retries after an execution failure."""

    @staticmethod
    def inject(
        simulation: PaymentSimulation,
        target_sequence: int,
        retry_count: int = 1,
    ) -> RetryScenario:
        if target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")

        if target_sequence >= len(simulation.events):
            raise IndexError(
                f"Target sequence {target_sequence} is outside the simulation."
            )

        if retry_count <= 0:
            raise ValueError("Retry count must be positive.")

        return RetryScenario(
            simulation_id=simulation.id,
            target_sequence=target_sequence,
            retry_count=retry_count,
        )
