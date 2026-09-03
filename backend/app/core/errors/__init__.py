from typing import Any


class DomainError(Exception):
    """Base exception for expected Financial Proof domain failures."""

    code = "DOMAIN_ERROR"
    status_code = 400

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationDomainError(DomainError):
    """Raised when domain input violates business validation."""

    code = "VALIDATION_ERROR"
    status_code = 422


class NotFoundError(DomainError):
    """Raised when a requested domain resource does not exist."""

    code = "NOT_FOUND"
    status_code = 404


class ConflictError(DomainError):
    """Raised when an operation conflicts with current state."""

    code = "CONFLICT"
    status_code = 409


class PolicyViolationError(DomainError):
    """Raised when a financial policy forbids an operation."""

    code = "POLICY_VIOLATION"
    status_code = 403


class InfrastructureError(DomainError):
    """Raised when a required infrastructure dependency fails."""

    code = "INFRASTRUCTURE_ERROR"
    status_code = 503
