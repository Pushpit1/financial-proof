from decimal import Decimal

import pytest

from app.domain.models.financial_blast_radius import FinancialExposure


def test_financial_exposure_defaults_to_zero() -> None:
    exposure = FinancialExposure()

    assert exposure.direct_loss == Decimal("0")
    assert exposure.duplicate_charge_exposure == Decimal("0")
    assert exposure.duplicate_fulfillment_exposure == Decimal("0")
    assert exposure.refund_exposure == Decimal("0")
    assert exposure.unauthorized_action_exposure == Decimal("0")
    assert exposure.actual_exposure == Decimal("0")
    assert exposure.maximum_exposure == Decimal("0")


def test_actual_exposure_is_sum_of_components() -> None:
    exposure = FinancialExposure(
        direct_loss=Decimal("100"),
        duplicate_charge_exposure=Decimal("200"),
        duplicate_fulfillment_exposure=Decimal("50"),
        refund_exposure=Decimal("25"),
        unauthorized_action_exposure=Decimal("75"),
        actual_exposure=Decimal("450"),
        maximum_exposure=Decimal("600"),
    )

    assert exposure.actual_exposure == Decimal("450")


def test_actual_exposure_must_match_components() -> None:
    with pytest.raises(
        ValueError,
        match="actual_exposure must equal",
    ):
        FinancialExposure(
            direct_loss=Decimal("100"),
            actual_exposure=Decimal("50"),
        )


def test_maximum_exposure_cannot_be_less_than_actual() -> None:
    with pytest.raises(
        ValueError,
        match="maximum_exposure cannot be less",
    ):
        FinancialExposure(
            direct_loss=Decimal("100"),
            actual_exposure=Decimal("100"),
            maximum_exposure=Decimal("50"),
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "direct_loss",
        "duplicate_charge_exposure",
        "duplicate_fulfillment_exposure",
        "refund_exposure",
        "unauthorized_action_exposure",
        "actual_exposure",
        "maximum_exposure",
    ],
)
def test_negative_exposure_is_rejected(field_name: str) -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        FinancialExposure(**{field_name: Decimal("-1")})


def test_exposure_is_immutable() -> None:
    exposure = FinancialExposure()

    with pytest.raises(
        AttributeError,
        match="frozen",
    ):
        exposure.direct_loss = Decimal("10")

def test_exposure_preserves_explanation() -> None:
    exposure = FinancialExposure(
        amount=Decimal("100"),
        currency="INR",
        explanation="Income shortfall caused financial exposure.",
    )

    assert exposure.explanation == (
        "Income shortfall caused financial exposure."
    )
