"""Tests for the financial contract decision persistence port."""

from uuid import uuid4

from app.application.ports.financial_contract_decision import (
    FinancialContractDecisionRepository,
)
from app.db.repositories.financial_contract_decision import (
    SqlAlchemyFinancialContractDecisionRepository,
)


def test_sqlalchemy_decision_repository_implements_port() -> None:
    assert issubclass(
        SqlAlchemyFinancialContractDecisionRepository,
        FinancialContractDecisionRepository,
    )


def test_decision_repository_port_is_abstract() -> None:
    assert FinancialContractDecisionRepository.__abstractmethods__ == {
        "save",
        "get_by_id",
        "list_by_contract",
    }


def test_missing_decision_returns_none(db) -> None:
    repository = SqlAlchemyFinancialContractDecisionRepository(db)

    assert repository.get_by_id(uuid4()) is None
