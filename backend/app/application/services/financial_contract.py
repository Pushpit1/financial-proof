"""Application service for financial contract workflows."""

from uuid import UUID

from app.application.ports.financial_contract import (
    FinancialContractRepository,
)
from app.application.ports.unit_of_work import FinancialUnitOfWorkPort
from app.core.errors.domain import NotFoundError
from app.domain.models.financial import FinancialContract


class FinancialContractApplicationService:
    """Coordinate financial contract workflows."""

    def __init__(
        self,
        unit_of_work: FinancialUnitOfWorkPort,
    ) -> None:
        self.unit_of_work = unit_of_work

    @property
    def repository(self) -> FinancialContractRepository:
        """Return the contract repository through the application port."""
        return self.unit_of_work.contracts

    def create_contract(
        self,
        contract: FinancialContract,
    ) -> FinancialContract:
        """Persist a financial contract."""
        with self.unit_of_work:
            return self.repository.add(contract)

    def get_contract(
        self,
        contract_id: UUID,
    ) -> FinancialContract | None:
        """Retrieve a financial contract by ID."""
        return self.repository.get_by_id(contract_id)

    def get_contract_version(
        self,
        name: str,
        version: int,
    ) -> FinancialContract | None:
        """Retrieve a specific financial contract version."""
        return self.repository.get_by_name_and_version(
            name,
            version,
        )

    def list_contract_versions(
        self,
        name: str,
    ) -> list[FinancialContract]:
        """List all versions of a financial contract."""
        return self.repository.list_by_name(name)

    def require_contract_version(
        self,
        name: str,
        version: int,
    ) -> FinancialContract:
        """Retrieve a contract version or raise a domain error."""
        contract = self.get_contract_version(name, version)

        if contract is None:
            raise NotFoundError(
                f"Financial contract '{name}' version "
                f"{version} was not found."
            )

        return contract



