from collections.abc import Callable

from app.domain.models.adversarial_scenario import AdversarialScenario


class AdversarialScenarioShrinker:
    """Deterministically minimize adversarial components."""

    @staticmethod
    def _with_components(
        scenario: AdversarialScenario,
        components: tuple[object, ...],
    ) -> AdversarialScenario:
        return AdversarialScenario(
            simulation_id=scenario.simulation_id,
            components=components,
        )

    @classmethod
    def shrink(
        cls,
        scenario: AdversarialScenario,
        reproduces_failure: Callable[[AdversarialScenario], bool],
    ) -> AdversarialScenario:
        """Remove unnecessary adversarial components deterministically."""
        if not reproduces_failure(scenario):
            raise ValueError(
                "Adversarial scenario shrinker requires an input that "
                "reproduces the failure."
            )

        current = scenario
        index = 0

        while index < len(current.components):
            candidate_components = (
                current.components[:index]
                + current.components[index + 1 :]
            )

            candidate = cls._with_components(
                current,
                candidate_components,
            )

            if reproduces_failure(candidate):
                current = candidate
            else:
                index += 1

        return current
