"""Repositories for financial contract persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports.financial_contract import (
    FinancialContractRepository,
)
from app.db.mappers.financial import (
    financial_contract_to_domain,
    financial_contract_to_model,
)
from app.db.models.financial import FinancialContractModel
from app.domain.models.financial import FinancialContract


class FinancialContractRepository(
    FinancialContractRepository,
):
    """SQLAlchemy implementation of the financial contract repository port."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, contract: FinancialContract) -> FinancialContract:
        """Persist a financial contract."""
        model = financial_contract_to_model(contract)
        self.session.add(model)
        self.session.flush()
        return financial_contract_to_domain(model)

    def get_by_id(
        self,
        contract_id: UUID,
    ) -> FinancialContract | None:
        """Get a financial contract by ID."""
        model = self.session.get(
            FinancialContractModel,
            contract_id,
        )

        if model is None:
            return None

        return financial_contract_to_domain(model)

    def get_by_name_and_version(
        self,
        name: str,
        version: int,
    ) -> FinancialContract | None:
        """Get a specific contract version by name."""
        statement = select(FinancialContractModel).where(
            FinancialContractModel.name == name,
            FinancialContractModel.version == version,
        )

        model = self.session.scalars(statement).first()

        if model is None:
            return None

        return financial_contract_to_domain(model)

    def list_by_name(
        self,
        name: str,
    ) -> list[FinancialContract]:
        """List all versions of a financial contract."""
        statement = (
            select(FinancialContractModel)
            .where(FinancialContractModel.name == name)
            .order_by(FinancialContractModel.version.asc())
        )

        return [
            financial_contract_to_domain(model)
            for model in self.session.scalars(statement).all()
        ]

