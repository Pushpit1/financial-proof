"""Tests for the financial contract application port."""

from uuid import uuid4

from app.application.ports.financial_contract import (
    FinancialContractRepository,
)
from app.db.repositories.financial import (
    FinancialContractRepository as SqlAlchemyFinancialContractRepository,
)


def test_sqlalchemy_contract_repository_has_required_port_operations() -> None:
    required_methods = {
        "add",
        "get_by_id",
        "get_by_name_and_version",
        "list_by_name",
    }

    assert required_methods.issubset(
        set(dir(SqlAlchemyFinancialContractRepository))
    )


def test_contract_port_declares_required_operations() -> None:
    assert hasattr(FinancialContractRepository, "add")
    assert hasattr(FinancialContractRepository, "get_by_id")
    assert hasattr(
        FinancialContractRepository,
        "get_by_name_and_version",
    )
    assert hasattr(FinancialContractRepository, "list_by_name")
    assert uuid4 is not None
