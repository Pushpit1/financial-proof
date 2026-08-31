"""Application ports for financial contracts."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.financial import FinancialContract


class FinancialContractRepository(ABC):
    """Persistence boundary for financial contracts."""

    @abstractmethod
    def add(self, contract: FinancialContract) -> None:
        """Persist a financial contract."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        contract_id: UUID,
    ) -> FinancialContract | None:
        """Retrieve a financial contract by ID."""
        raise NotImplementedError

    @abstractmethod
    def get_by_name_and_version(
        self,
        name: str,
        version: int,
    ) -> FinancialContract | None:
        """Retrieve a specific financial contract version."""
        raise NotImplementedError

    @abstractmethod
    def list_by_name(
        self,
        name: str,
    ) -> list[FinancialContract]:
        """Retrieve all versions of a financial contract."""
        raise NotImplementedError
