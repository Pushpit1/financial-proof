from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.financial import FinancialContractDecision


class FinancialContractDecisionRepository(ABC):
    """Persistence boundary for financial contract decisions."""

    @abstractmethod
    def save(
        self,
        decision: FinancialContractDecision,
    ) -> FinancialContractDecision:
        """Persist and return a decision."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        decision_id: UUID,
    ) -> FinancialContractDecision | None:
        """Retrieve a decision by identifier."""
        raise NotImplementedError
