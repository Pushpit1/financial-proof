from collections.abc import Sequence
from datetime import datetime, timedelta

from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationResult,
)
from app.domain.services.payment_simulation_runner import PaymentSimulationRunner


class PaymentSimulationBatchRunner:
    """Execute and replay independent payment simulations as a batch."""

    @staticmethod
    def run(
        simulations: Sequence[PaymentSimulation],
    ) -> tuple[SimulationResult, ...]:
        """Execute every simulation independently in input order."""

        return tuple(
            PaymentSimulationRunner.run(simulation)
            for simulation in simulations
        )

    @staticmethod
    def replay(
        simulations: Sequence[PaymentSimulation],
    ) -> tuple[SimulationResult, ...]:
        """Replay every simulation independently in input order."""

        return tuple(
            PaymentSimulationRunner.replay(simulation)
            for simulation in simulations
        )

    @staticmethod
    def build(
        seeds: Sequence[int],
        initial_payment: Payment,
        initial_order: PaymentOrder,
        event_count: int,
        start_time: datetime,
        step: timedelta = timedelta(seconds=1),
        allowed_events: Sequence[PaymentEvent] | None = None,
    ) -> tuple[PaymentSimulation, ...]:
        """Build a deterministic batch from a sequence of seeds."""

        simulations: list[PaymentSimulation] = []

        for seed in seeds:
            events = PaymentSimulationRunner.create_events(
                seed=seed,
                event_count=event_count,
                start_time=start_time,
                step=step,
                allowed_events=allowed_events,
            )

            simulations.append(
                PaymentSimulation(
                    seed=seed,
                    initial_payment=initial_payment,
                    initial_order=initial_order,
                    events=events,
                )
            )

        return tuple(simulations)

    @staticmethod
    def replay_matches(
        simulations: Sequence[PaymentSimulation],
        expected: Sequence[SimulationResult],
    ) -> bool:
        """Verify that batch replay reproduces every expected result."""

        if len(simulations) != len(expected):
            return False

        replayed = PaymentSimulationBatchRunner.replay(simulations)

        return all(
            actual == expected_result
            for actual, expected_result in zip(
                replayed,
                expected,
                strict=True,
            )
        )

