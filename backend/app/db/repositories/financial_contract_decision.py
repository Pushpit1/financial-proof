from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.mappers.financial import (
    financial_contract_decision_to_domain,
    financial_contract_decision_to_model,
)
from app.db.models.financial import FinancialContractDecisionModel
from app.domain.models.financial import FinancialContractDecision


class SqlAlchemyFinancialContractDecisionRepository:
    """SQLAlchemy implementation of the decision persistence port."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        decision: FinancialContractDecision,
    ) -> FinancialContractDecision:
        """Persist a decision and return its domain representation."""
        model = financial_contract_decision_to_model(decision)
        self.session.add(model)
        self.session.flush()
        return financial_contract_decision_to_domain(model)

    def get_by_id(
        self,
        decision_id: UUID,
    ) -> FinancialContractDecision | None:
        """Retrieve a decision by ID."""
        model = self.session.get(
            FinancialContractDecisionModel,
            decision_id,
        )

        if model is None:
            return None

        return financial_contract_decision_to_domain(model)

    def list_by_contract(
        self,
        contract_id: UUID,
    ) -> list[FinancialContractDecision]:
        """Retrieve decisions deterministically for a contract."""
        statement = (
            select(FinancialContractDecisionModel)
            .where(
                FinancialContractDecisionModel.contract_id
                == contract_id
            )
            .order_by(
                FinancialContractDecisionModel.evaluated_at.asc(),
                FinancialContractDecisionModel.id.asc(),
            )
        )

        return [
            financial_contract_decision_to_domain(model)
            for model in self.session.scalars(statement).all()
        ]
