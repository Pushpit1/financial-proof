"""Deterministic end-to-end Financial Proof demo runner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.demo.seed import DemoSeed, build_demo_seed
from app.demo.state import DemoState, DemoStateManager


@dataclass(frozen=True)
class DemoStepResult:
    """Immutable result for one demo workflow step."""

    number: int
    name: str
    status: str
    message: str
    data: dict[str, Any]


class DemoRunner:
    """Own the deterministic orchestration boundary for the demo."""

    STEP_NAMES = (
        "enter_business_rule",
        "compile_contract",
        "display_contract",
        "attack_payment_system",
        "run_many_executions",
        "find_violation",
        "display_counterexample",
        "shrink_counterexample",
        "calculate_financial_exposure",
        "ai_investigation",
        "display_root_cause",
        "apply_repair",
        "rerun_verification",
        "display_zero_violations",
        "activate_guardian",
        "attempt_unauthorized_refund",
        "show_blocked",
        "generate_financial_proof",
    )

    def __init__(
        self,
        state_manager: DemoStateManager | None = None,
    ) -> None:
        self.state_manager = state_manager or DemoStateManager()
        self.state = self.state_manager.state

    @property
    def seed(self) -> DemoSeed:
        """Return the canonical deterministic demo seed."""
        return self.state.seed

    def reset(self) -> DemoState:
        """Reset the demo to its deterministic initial state."""
        return self.state_manager.reset()

    def replay(self) -> DemoState:
        """Reset and return a clean deterministic replay state."""
        return self.reset()

    def step_names(self) -> tuple[str, ...]:
        """Return the canonical workflow ordering."""
        return self.STEP_NAMES

    def record_step(
        self,
        number: int,
        name: str,
        *,
        status: str = "pending",
        message: str = "",
        data: dict[str, Any] | None = None,
    ) -> DemoStepResult:
        """Record one orchestration step without mutating domain objects."""
        if number < 1 or number > len(self.STEP_NAMES):
            raise ValueError(f"Invalid demo step number: {number}.")

        expected_name = self.STEP_NAMES[number - 1]
        if name != expected_name:
            raise ValueError(
                f"Demo step {number} must be '{expected_name}', got '{name}'."
            )

        result = DemoStepResult(
            number=number,
            name=name,
            status=status,
            message=message,
            data=dict(data or {}),
        )

        self.state.step_results[number] = result
        return result

    def mark_success(
        self,
        number: int,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> DemoStepResult:
        """Record a successful demo step."""
        return self.record_step(
            number,
            self.STEP_NAMES[number - 1],
            status="success",
            message=message,
            data=data,
        )

    def mark_failed(
        self,
        number: int,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> DemoStepResult:
        """Record a failed demo step."""
        return self.record_step(
            number,
            self.STEP_NAMES[number - 1],
            status="failed",
            message=message,
            data=data,
        )

    def build_initial_context(self) -> dict[str, Any]:
        """Return stable input data for the first demo stages."""
        seed = self.seed
        return {
            "seed": seed.seed,
            "contract_id": str(seed.contract_id),
            "contract_name": seed.contract_name,
            "contract_version": seed.contract_version,
            "business_rule": seed.business_rule,
            "order_id": str(seed.order_id),
            "payment_id": str(seed.payment_id),
            "simulation_id": str(seed.simulation_id),
            "amount_minor": seed.amount_minor,
            "currency": seed.currency,
        }

    def ensure_seed(self) -> DemoSeed:
        """Ensure the state has a canonical deterministic seed."""
        if self.state.seed is None:
            self.state.seed = build_demo_seed()
        return self.state.seed
