from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.financial_blast_radius import FinancialBlastRadius


class FinancialBlastRadiusRepository(ABC):
    """Persistence boundary for financial blast-radius analyses."""

    @abstractmethod
    def save(
        self,
        analysis: FinancialBlastRadius,
    ) -> FinancialBlastRadius:
        """Persist a blast-radius analysis."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        analysis_id: UUID,
    ) -> FinancialBlastRadius | None:
        """Retrieve a blast-radius analysis by ID."""
        raise NotImplementedError
