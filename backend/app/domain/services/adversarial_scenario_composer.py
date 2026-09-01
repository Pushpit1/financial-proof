from app.domain.models.adversarial_scenario import (
    AdversarialScenario,
    AdversarialScenarioComponent,
)
from app.domain.models.payment_simulation import PaymentSimulation


class AdversarialScenarioComposer:
    """Build deterministic adversarial scenarios."""

    @staticmethod
    def _ordering_key(
        component: AdversarialScenarioComponent,
    ) -> tuple[int, str]:
        sequence = getattr(
            component,
            "target_sequence",
            getattr(component, "incoming_sequence", 0),
        )
        return sequence, type(component).__name__

    @staticmethod
    def compose(
        simulation: PaymentSimulation,
        *components: AdversarialScenarioComponent,
    ) -> AdversarialScenario:
        for component in components:
            if component.simulation_id != simulation.id:
                raise ValueError(
                    "Adversarial component belongs to a different simulation."
                )

        ordered_components = tuple(
            sorted(
                components,
                key=AdversarialScenarioComposer._ordering_key,
            )
        )

        return AdversarialScenario(
            simulation_id=simulation.id,
            components=ordered_components,
        )
