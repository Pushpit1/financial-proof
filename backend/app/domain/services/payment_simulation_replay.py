from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationResult,
)
from app.domain.services.payment_simulation_runner import PaymentSimulationRunner


class PaymentSimulationReplay:
    """Replay a previously recorded deterministic simulation."""

    @staticmethod
    def replay(simulation: PaymentSimulation) -> SimulationResult:
        return PaymentSimulationRunner.replay(simulation)
