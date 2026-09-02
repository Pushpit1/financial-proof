"""Deterministic demo state and reset services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.demo.seed import DemoSeed, build_demo_seed


@dataclass
class DemoState:
    """Mutable in-memory state for one deterministic demo run."""

    seed: DemoSeed
    compiled_contract: Any | None = None
    simulation: Any | None = None
    adversarial_simulation: Any | None = None
    verification_result: Any | None = None
    counterexample: Any | None = None
    financial_blast_radius: Any | None = None
    investigation: Any | None = None
    repair: Any | None = None
    guardian_evaluation: Any | None = None
    proof_certificate: Any | None = None
    violations: list[Any] = field(default_factory=list)
    step_results: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, seed: DemoSeed | None = None) -> DemoState:
        """Create a fresh demo state from the canonical seed."""
        return cls(seed=seed or build_demo_seed())

    def reset(self) -> DemoState:
        """Reset this state to a fresh deterministic demo state."""
        fresh = type(self).create(self.seed)
        self.__dict__.clear()
        self.__dict__.update(fresh.__dict__)
        return self

    def record_step(self, step: str, result: Any) -> None:
        """Record the result of one demo step."""
        self.step_results[step] = result

    def clear_runtime_results(self) -> None:
        """Clear all execution-derived demo state while preserving the seed."""
        self.compiled_contract = None
        self.simulation = None
        self.adversarial_simulation = None
        self.verification_result = None
        self.counterexample = None
        self.financial_blast_radius = None
        self.investigation = None
        self.repair = None
        self.guardian_evaluation = None
        self.proof_certificate = None
        self.violations.clear()
        self.step_results.clear()


class DemoStateManager:
    """Own and reset the canonical deterministic demo state."""

    def __init__(self, seed: DemoSeed | None = None) -> None:
        self._seed = seed or build_demo_seed()
        self._state = DemoState.create(self._seed)

    @property
    def state(self) -> DemoState:
        """Return the current demo state."""
        return self._state

    def reset(self) -> DemoState:
        """Replace the current state with a fresh deterministic state."""
        self._state = DemoState.create(self._seed)
        return self._state

    def reset_runtime(self) -> DemoState:
        """Clear runtime results while preserving the same seed."""
        self._state.clear_runtime_results()
        return self._state

    def snapshot(self) -> dict[str, Any]:
        """Return a lightweight state snapshot for diagnostics and UI."""
        state = self._state
        return {
            "seed": state.seed.seed,
            "contract_id": str(state.seed.contract_id),
            "order_id": str(state.seed.order_id),
            "payment_id": str(state.seed.payment_id),
            "simulation_id": str(state.seed.simulation_id),
            "has_compiled_contract": state.compiled_contract is not None,
            "has_simulation": state.simulation is not None,
            "has_adversarial_simulation": state.adversarial_simulation is not None,
            "has_verification_result": state.verification_result is not None,
            "has_counterexample": state.counterexample is not None,
            "has_financial_blast_radius": state.financial_blast_radius is not None,
            "has_investigation": state.investigation is not None,
            "has_repair": state.repair is not None,
            "has_guardian_evaluation": state.guardian_evaluation is not None,
            "has_proof_certificate": state.proof_certificate is not None,
            "violation_count": len(state.violations),
            "completed_steps": sorted(state.step_results),
        }
