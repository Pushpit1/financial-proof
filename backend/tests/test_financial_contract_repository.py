"""Tests for financial contract persistence repository."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models.financial import FinancialContractModel
from app.db.repositories.financial import FinancialContractRepository


def test_add_and_get_contract(db) -> None:
    repository = FinancialContractRepository(db)

    contract = FinancialContractModel(
        id=uuid4(),
        name="Income Verification Contract",
        version=1,
        minimum_confidence=0.80,
        minimum_supported_claim_ratio=0.90,
        required_claim_types=["income", "employment"],
    )

    repository.add(contract)
    db.commit()

    restored = repository.get_by_id(contract.id)

    assert restored is not None
    assert restored.id == contract.id
    assert restored.name == "Income Verification Contract"
    assert restored.version == 1


def test_get_contract_by_name_and_version(db) -> None:
    repository = FinancialContractRepository(db)

    contract = FinancialContractModel(
        id=uuid4(),
        name="Income Verification Contract",
        version=2,
        minimum_confidence=0.85,
        minimum_supported_claim_ratio=0.95,
        required_claim_types=["income"],
    )

    repository.add(contract)
    db.commit()

    restored = repository.get_by_name_and_version(
        "Income Verification Contract",
        2,
    )

    assert restored is not None
    assert restored.id == contract.id
    assert restored.version == 2


def test_get_contract_by_name_and_version_returns_none_for_missing(
    db,
) -> None:
    repository = FinancialContractRepository(db)

    restored = repository.get_by_name_and_version(
        "Does Not Exist",
        99,
    )

    assert restored is None


def test_list_contract_versions_is_ordered(db) -> None:
    repository = FinancialContractRepository(db)

    contract_v2 = FinancialContractModel(
        id=uuid4(),
        name="Income Verification Contract",
        version=2,
        minimum_confidence=0.85,
        minimum_supported_claim_ratio=0.95,
        required_claim_types=["income"],
    )

    contract_v1 = FinancialContractModel(
        id=uuid4(),
        name="Income Verification Contract",
        version=1,
        minimum_confidence=0.80,
        minimum_supported_claim_ratio=0.90,
        required_claim_types=["income", "employment"],
    )

    repository.add(contract_v2)
    repository.add(contract_v1)
    db.commit()

    contracts = repository.list_by_name(
        "Income Verification Contract"
    )

    assert [contract.version for contract in contracts] == [1, 2]


def test_duplicate_contract_version_is_rejected(db) -> None:
    repository = FinancialContractRepository(db)

    first = FinancialContractModel(
        id=uuid4(),
        name="Immutable Contract",
        version=1,
        minimum_confidence=0.80,
        minimum_supported_claim_ratio=0.90,
        required_claim_types=["income"],
    )

    second = FinancialContractModel(
        id=uuid4(),
        name="Immutable Contract",
        version=1,
        minimum_confidence=0.95,
        minimum_supported_claim_ratio=0.99,
        required_claim_types=["employment"],
    )

    repository.add(first)
    db.commit()

    repository.add(second)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()

    stored = repository.get_by_name_and_version(
        "Immutable Contract",
        1,
    )

    assert stored is not None
    assert stored.id == first.id
    assert stored.minimum_confidence == Decimal("0.8000")
    assert stored.minimum_supported_claim_ratio == Decimal("0.9000")
    assert stored.required_claim_types == ["income"]
