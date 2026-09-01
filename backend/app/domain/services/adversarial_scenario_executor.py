from dataclasses import dataclass
from uuid import UUID

from app.domain.models.adversarial_scenario import AdversarialScenario
from app.domain.models.adversarial_simulation import (
    DuplicateEventAttack,
    OutOfOrderEventAttack,
)
from app.domain.models.lost_response import LostResponseScenario
from app.domain.models.partial_failure import PartialFailureScenario
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
    SimulationResult,
)
from app.domain.models.retry import RetryScenario
from app.domain.models.stale_worker_state import StaleWorkerStateAttack
from app.domain.models.worker_crash import WorkerCrashScenario
from app.domain.services.payment_simulation_runner import PaymentSimulationRunner


class AdversarialOutcomeStatus(str):
    """Deterministic status of an adversarial component."""

    APPLIED = "applied"


@dataclass(frozen=True)
class AdversarialComponentOutcome:
    """Result of applying one adversarial component."""

    component_type: str
    target_sequence: int | None
    status: str


@dataclass(frozen=True)
class AdversarialExecutionResult:
    """Deterministic result of executing an adversarial scenario."""

    simulation_id: UUID
    baseline: SimulationResult
    adversarial_simulation: PaymentSimulation
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

    @property
    def adversarial_result(self) -> SimulationResult:
        """Execute the transformed simulation deterministically."""

        return PaymentSimulationRunner.run(self.adversarial_simulation)


class AdversarialScenarioExecutor:
    """Execute composed adversarial scenarios deterministically."""

    @staticmethod
    def _clone_event(
        event: SimulationEvent,
        sequence: int,
    ) -> SimulationEvent:
        return SimulationEvent(
            sequence=sequence,
            event=event.event,
            occurred_at=event.occurred_at,
            id=event.id,
        )

    @classmethod
    def _apply_out_of_order(
        cls,
        simulation: PaymentSimulation,
        attack: OutOfOrderEventAttack,
    ) -> PaymentSimulation:
        events = list(simulation.events)

        moved_event = events.pop(attack.source_sequence)
        events.insert(attack.target_sequence, moved_event)

        transformed_events = tuple(
            cls._clone_event(event, sequence)
            for sequence, event in enumerate(events)
        )

        return PaymentSimulation(
            seed=simulation.seed,
            initial_payment=simulation.initial_payment,
            initial_order=simulation.initial_order,
            events=transformed_events,
            id=simulation.id,
        )

    @classmethod
    def _apply_duplicate(
        cls,
        simulation: PaymentSimulation,
        attack: DuplicateEventAttack,
    ) -> PaymentSimulation:
        events = list(simulation.events)
        duplicated = events[attack.target_sequence]

        events.insert(attack.target_sequence + 1, duplicated)

        transformed_events = tuple(
            cls._clone_event(event, sequence)
            for sequence, event in enumerate(events)
        )

        return PaymentSimulation(
            seed=simulation.seed,
            initial_payment=simulation.initial_payment,
            initial_order=simulation.initial_order,
            events=transformed_events,
            id=simulation.id,
        )

    @staticmethod
    def _validate_target(
        simulation: PaymentSimulation,
        target: int | None,
    ) -> None:
        if target is not None and target >= len(simulation.events):
            raise ValueError(
                f"Adversarial component targets nonexistent sequence {target}."
            )

    @classmethod
    def execute(
        cls,
        simulation: PaymentSimulation,
        scenario: AdversarialScenario,
    ) -> AdversarialExecutionResult:
        if scenario.simulation_id != simulation.id:
            raise ValueError(
                "Adversarial scenario belongs to a different simulation."
            )

        baseline = PaymentSimulationRunner.run(simulation)
        current = simulation
        outcomes: list[AdversarialComponentOutcome] = []

        for component in scenario.components:
            target = getattr(
                component,
                "target_sequence",
                getattr(component, "incoming_sequence", None),
            )

            cls._validate_target(current, target)

            if isinstance(component, OutOfOrderEventAttack):
                current = cls._apply_out_of_order(current, component)
            elif isinstance(component, DuplicateEventAttack):
                current = cls._apply_duplicate(current, component)
            elif isinstance(
                component,
                (
                    LostResponseScenario,
                    PartialFailureScenario,
                    RetryScenario,
                    StaleWorkerStateAttack,
                    WorkerCrashScenario,
                ),
            ):
                pass
            else:
                raise TypeError(
                    f"Unsupported adversarial component: "
                    f"{type(component).__name__}"
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
            adversarial_simulation=current,
            scenario=scenario,
            outcomes=tuple(outcomes),
        )
