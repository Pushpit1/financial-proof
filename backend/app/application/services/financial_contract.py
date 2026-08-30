"""Application service for financial contract workflows."""

from uuid import UUID

from app.core.errors.domain import NotFoundError
from app.db.mappers.financial import (
    financial_contract_to_domain,
    financial_contract_to_model,
)
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.models.financial import FinancialContract


class FinancialContractApplicationService:
    """Coordinate financial contract persistence as an application operation."""

    def __init__(
        self,
        unit_of_work: FinancialUnitOfWork,
    ) -> None:
        self.unit_of_work = unit_of_work

    def create_contract(
        self,
        contract: FinancialContract,
    ) -> FinancialContract:
        """Persist a financial contract."""
        with self.unit_of_work:
            self.unit_of_work.contracts.add(
                financial_contract_to_model(contract)
            )

        return contract

    def get_contract(
        self,
        contract_id: UUID,
    ) -> FinancialContract | None:
        """Retrieve a financial contract by ID."""
        model = self.unit_of_work.contracts.get_by_id(contract_id)

        if model is None:
            return None

        return financial_contract_to_domain(model)

    def get_contract_version(
        self,
        name: str,
        version: int,
    ) -> FinancialContract | None:
        """Retrieve a specific financial contract version."""
        model = self.unit_of_work.contracts.get_by_name_and_version(
            name,
            version,
        )

        if model is None:
            return None

        return financial_contract_to_domain(model)

    def list_contract_versions(
        self,
        name: str,
    ) -> list[FinancialContract]:
        """List all versions of a financial contract."""
        models = self.unit_of_work.contracts.list_by_name(name)

        return [
            financial_contract_to_domain(model)
            for model in models
        ]

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