from dataclasses import dataclass
from uuid import UUID

from app.domain.models.adversarial_simulation import AdversarialAttack
from app.domain.models.lost_response import LostResponseScenario
from app.domain.models.partial_failure import PartialFailureScenario
from app.domain.models.retry import RetryScenario
from app.domain.models.stale_worker_state import StaleWorkerStateAttack
from app.domain.models.worker_crash import WorkerCrashScenario

AdversarialScenarioComponent = (
    AdversarialAttack
    | LostResponseScenario
    | RetryScenario
    | WorkerCrashScenario
    | PartialFailureScenario
    | StaleWorkerStateAttack
)


@dataclass(frozen=True)
class AdversarialScenario:
    """Immutable composition of deterministic adversarial behaviors."""

    simulation_id: UUID
    components: tuple[AdversarialScenarioComponent, ...]

    def __post_init__(self) -> None:
        for component in self.components:
            if component.simulation_id != self.simulation_id:
                raise ValueError(
                    "All adversarial components must target the same simulation."
                )

            if isinstance(component, StaleWorkerStateAttack):
                if component.incoming_sequence > component.worker_sequence:
                    raise ValueError(
                        "Incoming sequence cannot be newer than worker state."
                    )

        targets: list[int] = []

        for component in self.components:
            target = getattr(component, "target_sequence", None)

            if target is not None:
                targets.append(target)

        if len(targets) != len(set(targets)):
            raise ValueError(
                "Multiple adversarial components target the same sequence."
            )
