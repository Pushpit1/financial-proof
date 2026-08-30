"""Tests for financial contract domain invariants."""

from decimal import Decimal

import pytest

from app.domain.enums.financial import ClaimType
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import ConfidenceScore


def test_financial_contract_defaults() -> None:
    contract = FinancialContract(
        name="Standard Financial Review",
    )

    assert contract.name == "Standard Financial Review"
    assert contract.version == 1
    assert contract.minimum_confidence == ConfidenceScore(
        Decimal("0")
    )
    assert contract.minimum_supported_claim_ratio == Decimal("1")
    assert contract.required_claim_types == ()


def test_financial_contract_supports_required_claim_types() -> None:
    contract = FinancialContract(
        name="Income Verification",
        version=2,
        minimum_confidence=ConfidenceScore(
            Decimal("0.80")
        ),
        minimum_supported_claim_ratio=Decimal("0.90"),
        required_claim_types=(
            ClaimType.INCOME,
            ClaimType.EMPLOYMENT,
        ),
    )

    assert contract.version == 2
    assert contract.minimum_confidence == ConfidenceScore(
        Decimal("0.80")
    )
    assert contract.minimum_supported_claim_ratio == Decimal("0.90")
    assert contract.required_claim_types == (
        ClaimType.INCOME,
        ClaimType.EMPLOYMENT,
    )


def test_financial_contract_rejects_empty_name() -> None:
    with pytest.raises(
        ValueError,
        match="Contract name cannot be empty",
    ):
        FinancialContract(name="")


def test_financial_contract_rejects_whitespace_name() -> None:
    with pytest.raises(
        ValueError,
        match="Contract name cannot be empty",
    ):
        FinancialContract(name="   ")


def test_financial_contract_rejects_invalid_version() -> None:
    with pytest.raises(
        ValueError,
        match="Contract version must be at least 1",
    ):
        FinancialContract(
            name="Invalid Version",
            version=0,
        )


@pytest.mark.parametrize(
    "ratio",
    [
        Decimal("-0.01"),
        Decimal("1.01"),
    ],
)
def test_financial_contract_rejects_invalid_supported_claim_ratio(
    ratio: Decimal,
) -> None:
    with pytest.raises(
        ValueError,
        match="Minimum supported claim ratio must be between 0 and 1",
    ):
        FinancialContract(
            name="Invalid Ratio",
            minimum_supported_claim_ratio=ratio,
        )


def test_financial_contract_is_immutable() -> None:
    contract = FinancialContract(
        name="Immutable Contract",
    )

    with pytest.raises(AttributeError):
        contract.name = "Changed"  # type: ignore[misc]
