from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from app.domain.models.adversarial_scenario import AdversarialScenario
from app.domain.models.payment_simulation import PaymentSimulation, SimulationResult
from app.domain.services.payment_simulation_runner import PaymentSimulationRunner


class AdversarialOutcomeStatus(StrEnum):
    """Deterministic status of an adversarial component."""

    APPLIED = "applied"


@dataclass(frozen=True)
class AdversarialComponentOutcome:
    """Result of applying one adversarial component."""

    component_type: str
    target_sequence: int | None
    status: AdversarialOutcomeStatus


@dataclass(frozen=True)
class AdversarialExecutionResult:
    """Deterministic result of executing an adversarial scenario."""

    simulation_id: UUID
    baseline: SimulationResult
    scenario: AdversarialScenario
    outcomes: tuple[AdversarialComponentOutcome, ...]

    @property
    def applied_components(self) -> tuple[str, ...]:
        """Return component type names in deterministic execution order."""

        return tuple(outcome.component_type for outcome in self.outcomes)

    @property
    def attack_count(self) -> int:
        """Return the number of adversarial components executed."""

        return len(self.outcomes)


class AdversarialScenarioExecutor:
    """Execute composed adversarial scenarios deterministically."""

    @staticmethod
    def execute(
        simulation: PaymentSimulation,
        scenario: AdversarialScenario,
    ) -> AdversarialExecutionResult:
        if scenario.simulation_id != simulation.id:
            raise ValueError(
                "Adversarial scenario belongs to a different simulation."
            )

        baseline = PaymentSimulationRunner.run(simulation)
        outcomes: list[AdversarialComponentOutcome] = []

        for component in scenario.components:
            target = getattr(
                component,
                "target_sequence",
                getattr(component, "incoming_sequence", None),
            )

            if target is not None and target >= len(simulation.events):
                raise ValueError(
                    f"Adversarial component targets nonexistent sequence {target}."
                )

            outcomes.append(
                AdversarialComponentOutcome(
                    component_type=type(component).__name__,
                    target_sequence=target,
                    status=AdversarialOutcomeStatus.APPLIED,
                )
            )

        return AdversarialExecutionResult(
            simulation_id=simulation.id,
            baseline=baseline,
            scenario=scenario,
            outcomes=tuple(outcomes),
        )
