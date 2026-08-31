from abc import ABC, abstractmethod

from app.application.ports.financial_contract import (
    FinancialContractRepository,
)
from app.application.ports.financial_contract_decision import (
    FinancialContractDecisionRepository,
)
from app.application.ports.financial_proof import (
    FinancialProofRepositoryPort,
)
from app.application.ports.webhook_event import (
    WebhookEventRepositoryPort,
)


class FinancialUnitOfWorkPort(ABC):
    """Application boundary for coordinating financial persistence."""

    financial_proofs: FinancialProofRepositoryPort
    contracts: FinancialContractRepository
    decisions: FinancialContractDecisionRepository
    webhook_events: WebhookEventRepositoryPort

    @abstractmethod
    def flush(self) -> None:
        """Flush pending persistence changes."""
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        """Roll back the current transaction."""
        raise NotImplementedError

    @abstractmethod
    def __enter__(self) -> "FinancialUnitOfWorkPort":
        """Enter the transaction boundary."""
        raise NotImplementedError

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Exit the transaction boundary."""
        raise NotImplementedError
