"""Tests for the financial contract application service."""

from decimal import Decimal

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