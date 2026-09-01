from dataclasses import dataclass

from app.domain.enums.financial_guardian import GuardianDecision


@dataclass(frozen=True)
class GuardianEvaluation:
    """Immutable result of one runtime financial guardian evaluation."""

    decision: GuardianDecision
    rule: str
    reason: str

    def __post_init__(self) -> None:
        if not self.rule.strip():
            raise ValueError("Guardian rule cannot be empty.")

        if not self.reason.strip():
            raise ValueError("Guardian reason cannot be empty.")
