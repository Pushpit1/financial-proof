from app.domain.models.payment_simulation import PaymentSimulation
from app.domain.models.worker_crash import WorkerCrashScenario


class WorkerCrashInjector:
    """Inject deterministic worker crash/restart behavior."""

    @staticmethod
    def inject(
        simulation: PaymentSimulation,
        target_sequence: int,
    ) -> WorkerCrashScenario:
        if target_sequence < 0:
            raise ValueError("Target sequence cannot be negative.")

        if target_sequence >= len(simulation.events):
            raise IndexError(
                f"Target sequence {target_sequence} is outside the simulation."
            )

        return WorkerCrashScenario(
            simulation_id=simulation.id,
            target_sequence=target_sequence,
        )
