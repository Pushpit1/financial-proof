from enum import StrEnum


class GuardianDecision(StrEnum):
    """Deterministic decision produced by the runtime financial guardian."""

    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"
