"""Tests for the financial contract application service."""

from decimal import Decimal

import pytest

from app.application.services.financial_contract import (
    FinancialContractApplicationService,
)
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.enums.financial import ClaimType
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import ConfidenceScore


def create_service(session) -> FinancialContractApplicationService:
    """Create a contract application service for a test session."""
    return FinancialContractApplicationService(
        FinancialUnitOfWork(session)
    )


def test_create_contract_persists_and_returns_domain_contract(
    db,
) -> None:
    service = create_service(db)

    contract = FinancialContract(
        name="Income Verification Contract",
        version=1,
        minimum_confidence=ConfidenceScore(
            Decimal("0.80")
        ),
        minimum_supported_claim_ratio=Decimal("0.90"),
        required_claim_types=(
            ClaimType.INCOME,
            ClaimType.EMPLOYMENT,
        ),
    )

    created = service.create_contract(contract)

    assert created == contract

    restored = service.get_contract(contract.id)

    assert restored == contract


def test_get_contract_version_returns_domain_contract(
    db,
) -> None:
    service = create_service(db)

    contract = FinancialContract(
        name="Income Verification Contract",
        version=2,
        minimum_confidence=ConfidenceScore(
            Decimal("0.85")
        ),
        minimum_supported_claim_ratio=Decimal("0.95"),
        required_claim_types=(
            ClaimType.INCOME,
        ),
    )

    service.create_contract(contract)

    restored = service.get_contract_version(
        "Income Verification Contract",
        2,
    )

    assert restored == contract


def test_get_contract_version_returns_none_when_missing(
    db,
) -> None:
    service = create_service(db)

    restored = service.get_contract_version(
        "Does Not Exist",
        99,
    )

    assert restored is None


def test_list_contract_versions_returns_domain_objects_in_order(
    db,
) -> None:
    service = create_service(db)

    contract_v2 = FinancialContract(
        name="Income Verification Contract",
        version=2,
        minimum_confidence=ConfidenceScore(
            Decimal("0.85")
        ),
        minimum_supported_claim_ratio=Decimal("0.95"),
        required_claim_types=(ClaimType.INCOME,),
    )

    contract_v1 = FinancialContract(
        name="Income Verification Contract",
        version=1,
        minimum_confidence=ConfidenceScore(
            Decimal("0.80")
        ),
        minimum_supported_claim_ratio=Decimal("0.90"),
        required_claim_types=(
            ClaimType.INCOME,
            ClaimType.EMPLOYMENT,
        ),
    )

    service.create_contract(contract_v2)
    service.create_contract(contract_v1)

    contracts = service.list_contract_versions(
        "Income Verification Contract"
    )

    assert [contract.version for contract in contracts] == [1, 2]
    assert all(
        isinstance(contract, FinancialContract)
        for contract in contracts
    )


def test_require_contract_version_raises_when_missing(
    db,
) -> None:
    service = create_service(db)

    try:
        service.require_contract_version(
            "Does Not Exist",
            99,
        )
    except Exception as exc:
        assert "version 99 was not found" in str(exc)
    else:
        raise AssertionError(
            "Expected missing contract to raise."
        )

def test_create_contract_rejects_duplicate_version(db) -> None:
    from sqlalchemy.exc import IntegrityError

    service = create_service(db)

    contract = FinancialContract(
        name="Duplicate Service Contract",
        version=1,
        minimum_confidence=ConfidenceScore(
            Decimal("0.80"),
        ),
        minimum_supported_claim_ratio=Decimal("0.90"),
        required_claim_types=(ClaimType.INCOME,),
    )

    service.create_contract(contract)

    duplicate = FinancialContract(
        name="Duplicate Service Contract",
        version=1,
        minimum_confidence=ConfidenceScore(
            Decimal("0.95"),
        ),
        minimum_supported_claim_ratio=Decimal("0.99"),
        required_claim_types=(ClaimType.EMPLOYMENT,),
    )

    try:
        service.create_contract(duplicate)
    except IntegrityError:
        db.rollback()
    else:
        raise AssertionError(
            "Expected duplicate contract version to raise IntegrityError."
        )

    restored = service.get_contract_version(
        "Duplicate Service Contract",
        1,
    )

    assert restored is not None
    assert restored.id == contract.id
    assert restored.minimum_confidence == ConfidenceScore(
        Decimal("0.80"),
    )
    assert restored.minimum_supported_claim_ratio == Decimal("0.9000")
    assert restored.required_claim_types == (ClaimType.INCOME,)

def test_get_contract_by_id_returns_persisted_contract(db) -> None:
    service = create_service(db)

    contract = FinancialContract(
        name="ID Resolution Contract",
        version=7,
        minimum_confidence=ConfidenceScore(
            Decimal("0.88"),
        ),
        minimum_supported_claim_ratio=Decimal("0.93"),
        required_claim_types=(ClaimType.INCOME, ClaimType.EMPLOYMENT),
    )

    created = service.create_contract(contract)

    restored = service.get_contract(created.id)

    assert restored is not None
    assert restored.id == created.id
    assert restored.name == "ID Resolution Contract"
    assert restored.version == 7
    assert restored.minimum_confidence == ConfidenceScore(
        Decimal("0.88"),
    )
    assert restored.minimum_supported_claim_ratio == Decimal("0.9300")
    assert restored.required_claim_types == (
        ClaimType.INCOME,
        ClaimType.EMPLOYMENT,
    )


def test_get_contract_version_resolves_exact_version(db) -> None:
    service = create_service(db)

    contract_v1 = FinancialContract(
        name="Version Resolution Contract",
        version=1,
        minimum_confidence=ConfidenceScore(
            Decimal("0.80"),
        ),
        minimum_supported_claim_ratio=Decimal("0.90"),
        required_claim_types=(ClaimType.INCOME,),
    )

    contract_v2 = FinancialContract(
        name="Version Resolution Contract",
        version=2,
        minimum_confidence=ConfidenceScore(
            Decimal("0.95"),
        ),
        minimum_supported_claim_ratio=Decimal("0.98"),
        required_claim_types=(ClaimType.EMPLOYMENT,),
    )

    created_v1 = service.create_contract(contract_v1)
    created_v2 = service.create_contract(contract_v2)

    resolved_v1 = service.get_contract_version(
        "Version Resolution Contract",
        1,
    )
    resolved_v2 = service.get_contract_version(
        "Version Resolution Contract",
        2,
    )

    assert resolved_v1 is not None
    assert resolved_v2 is not None

    assert resolved_v1.id == created_v1.id
    assert resolved_v1.version == 1
    assert resolved_v1.minimum_confidence == ConfidenceScore(
        Decimal("0.80"),
    )

    assert resolved_v2.id == created_v2.id
    assert resolved_v2.version == 2
    assert resolved_v2.minimum_confidence == ConfidenceScore(
        Decimal("0.95"),
    )


def test_get_contract_by_id_returns_none_when_missing(db) -> None:
    from uuid import uuid4

    service = create_service(db)

    assert service.get_contract(uuid4()) is None

def test_create_contract_rejects_invalid_confidence(db) -> None:
    service = create_service(db)

    with pytest.raises(ValueError):
        service.create_contract(
            FinancialContract(
                name="Invalid Confidence Contract",
                version=1,
                minimum_confidence=ConfidenceScore(
                    Decimal("1.01"),
                ),
                minimum_supported_claim_ratio=Decimal("0.90"),
                required_claim_types=(ClaimType.INCOME,),
            )
        )


def test_create_contract_rejects_invalid_claim_ratio(db) -> None:
    service = create_service(db)

    with pytest.raises(ValueError):
        service.create_contract(
            FinancialContract(
                name="Invalid Ratio Contract",
                version=1,
                minimum_confidence=ConfidenceScore(
                    Decimal("0.80"),
                ),
                minimum_supported_claim_ratio=Decimal("-0.01"),
                required_claim_types=(ClaimType.INCOME,),
            )
        )


def test_create_contract_rejects_empty_name(db) -> None:
    service = create_service(db)

    with pytest.raises(ValueError):
        service.create_contract(
            FinancialContract(
                name="",
                version=1,
                minimum_confidence=ConfidenceScore(
                    Decimal("0.80"),
                ),
                minimum_supported_claim_ratio=Decimal("0.90"),
                required_claim_types=(ClaimType.INCOME,),
            )
        )


def test_create_contract_rejects_invalid_version(db) -> None:
    service = create_service(db)

    with pytest.raises(ValueError):
        service.create_contract(
            FinancialContract(
                name="Invalid Version Contract",
                version=0,
                minimum_confidence=ConfidenceScore(
                    Decimal("0.80"),
                ),
                minimum_supported_claim_ratio=Decimal("0.90"),
                required_claim_types=(ClaimType.INCOME,),
            )
        )
