"""Application ports for financial contract decisions."""

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
        """Persist a financial contract decision."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        decision_id: UUID,
    ) -> FinancialContractDecision | None:
        """Retrieve a decision by ID."""
        raise NotImplementedError

    @abstractmethod
    def list_by_contract(
        self,
        contract_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FinancialContractDecision]:
        """Retrieve a page of decisions deterministically."""
        raise NotImplementedError
