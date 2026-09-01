from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.models.financial_blast_radius import (
    FinancialBlastRadius,
    FinancialBlastRadiusSeverity,
    FinancialBlastRadiusSeverityPolicy,
    FinancialExposure,
)


def test_financial_exposure_normalizes_currency() -> None:
    exposure = FinancialExposure(
        field="monthly_income",
        amount=Decimal("25000"),
        currency="inr",
    )

    assert exposure.currency == "INR"
    assert exposure.amount == Decimal("25000")


def test_financial_exposure_is_immutable() -> None:
    exposure = FinancialExposure(
        field="monthly_income",
        amount=Decimal("25000"),
        currency="INR",
    )

    with pytest.raises(AttributeError):
        exposure.amount = Decimal("50000")  # type: ignore[misc]


def test_financial_exposure_rejects_negative_amount() -> None:
    with pytest.raises(
        ValueError,
        match="Financial exposure amount cannot be negative",
    ):
        FinancialExposure(
            field="monthly_income",
            amount=Decimal("-1"),
            currency="INR",
        )


def test_financial_exposure_rejects_invalid_currency() -> None:
    with pytest.raises(
        ValueError,
        match="Financial exposure currency must be a 3-letter ISO code",
    ):
        FinancialExposure(
            field="monthly_income",
            amount=Decimal("100"),
            currency="IN",
        )


def test_blast_radius_aggregates_exposure_by_currency() -> None:
    source_id = uuid4()

    result = FinancialBlastRadius.from_exposures(
        source_id,
        (
            FinancialExposure(
                field="income",
                amount=Decimal("50000"),
                currency="INR",
            ),
            FinancialExposure(
                field="expense",
                amount=Decimal("10000"),
                currency="INR",
            ),
            FinancialExposure(
                field="usd_balance",
                amount=Decimal("100"),
                currency="USD",
            ),
        ),
    )

    assert result.source_id == source_id
    assert result.exposure_count == 3
    assert result.total_exposure_by_currency == {
        "INR": Decimal("60000"),
        "USD": Decimal("100"),
    }
    assert result.currencies == ("INR", "USD")


def test_blast_radius_tracks_unique_affected_fields() -> None:
    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (
            FinancialExposure(
                field="income",
                amount=Decimal("50000"),
                currency="INR",
            ),
            FinancialExposure(
                field="income",
                amount=Decimal("10000"),
                currency="INR",
            ),
            FinancialExposure(
                field="balance",
                amount=Decimal("25000"),
                currency="INR",
            ),
        ),
    )

    assert result.affected_fields == ("income", "balance")


def test_total_exposure_works_for_single_currency() -> None:
    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (
            FinancialExposure(
                field="income",
                amount=Decimal("50000"),
                currency="INR",
            ),
            FinancialExposure(
                field="balance",
                amount=Decimal("25000"),
                currency="INR",
            ),
        ),
    )

    assert result.total_exposure == Decimal("75000")


def test_total_exposure_rejects_mixed_currencies() -> None:
    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (
            FinancialExposure(
                field="income",
                amount=Decimal("50000"),
                currency="INR",
            ),
            FinancialExposure(
                field="balance",
                amount=Decimal("100"),
                currency="USD",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Total exposure cannot combine multiple currencies",
    ):
        _ = result.total_exposure


def test_empty_blast_radius_is_valid() -> None:
    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (),
    )

    assert result.exposure_count == 0
    assert result.affected_fields == ()
    assert result.currencies == ()
    assert result.total_exposure == Decimal("0")


def make_policy() -> FinancialBlastRadiusSeverityPolicy:
    return FinancialBlastRadiusSeverityPolicy(
        low_threshold=Decimal("10000"),
        medium_threshold=Decimal("50000"),
        high_threshold=Decimal("100000"),
        critical_threshold=Decimal("500000"),
    )


def test_severity_policy_classifies_boundaries_deterministically() -> None:
    policy = make_policy()

    assert policy.classify(Decimal("0")) is FinancialBlastRadiusSeverity.NONE
    assert policy.classify(Decimal("9999.99")) is FinancialBlastRadiusSeverity.NONE
    assert policy.classify(Decimal("10000")) is FinancialBlastRadiusSeverity.LOW
    assert policy.classify(Decimal("49999.99")) is FinancialBlastRadiusSeverity.LOW
    assert policy.classify(Decimal("50000")) is FinancialBlastRadiusSeverity.MEDIUM
    assert policy.classify(Decimal("99999.99")) is FinancialBlastRadiusSeverity.MEDIUM
    assert policy.classify(Decimal("100000")) is FinancialBlastRadiusSeverity.HIGH
    assert policy.classify(Decimal("499999.99")) is FinancialBlastRadiusSeverity.HIGH
    assert policy.classify(Decimal("500000")) is FinancialBlastRadiusSeverity.CRITICAL


def test_blast_radius_reports_severity() -> None:
    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (
            FinancialExposure(
                field="income",
                amount=Decimal("75000"),
                currency="INR",
            ),
        ),
    )

    assert result.severity(make_policy()) is FinancialBlastRadiusSeverity.MEDIUM


def test_empty_blast_radius_has_no_severity() -> None:
    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (),
    )

    assert result.severity(make_policy()) is FinancialBlastRadiusSeverity.NONE


def test_mixed_currency_severity_is_rejected() -> None:
    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (
            FinancialExposure(
                field="income",
                amount=Decimal("50000"),
                currency="INR",
            ),
            FinancialExposure(
                field="balance",
                amount=Decimal("100"),
                currency="USD",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Severity cannot combine exposures from multiple currencies",
    ):
        result.severity(make_policy())


def test_invalid_severity_threshold_order_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="monotonically increasing",
    ):
        FinancialBlastRadiusSeverityPolicy(
            low_threshold=Decimal("50000"),
            medium_threshold=Decimal("10000"),
            high_threshold=Decimal("100000"),
            critical_threshold=Decimal("500000"),
        )

def test_ranked_exposures_prioritize_severity_then_amount() -> None:
    policy = FinancialBlastRadiusSeverityPolicy(
        low_threshold=Decimal("10000"),
        medium_threshold=Decimal("50000"),
        high_threshold=Decimal("100000"),
        critical_threshold=Decimal("500000"),
    )

    low = FinancialExposure(
        field="small",
        amount=Decimal("20000"),
        currency="INR",
    )
    medium = FinancialExposure(
        field="medium",
        amount=Decimal("60000"),
        currency="INR",
    )
    high = FinancialExposure(
        field="large",
        amount=Decimal("150000"),
        currency="INR",
    )

    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (low, medium, high),
    )

    assert result.ranked_exposures(policy) == (
        high,
        medium,
        low,
    )


def test_ranked_exposures_use_amount_as_tie_breaker() -> None:
    policy = FinancialBlastRadiusSeverityPolicy(
        low_threshold=Decimal("10000"),
        medium_threshold=Decimal("50000"),
        high_threshold=Decimal("100000"),
        critical_threshold=Decimal("500000"),
    )

    smaller = FinancialExposure(
        field="smaller",
        amount=Decimal("60000"),
        currency="INR",
    )
    larger = FinancialExposure(
        field="larger",
        amount=Decimal("90000"),
        currency="INR",
    )

    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (smaller, larger),
    )

    assert result.ranked_exposures(policy) == (
        larger,
        smaller,
    )


def test_ranked_exposures_use_field_as_deterministic_tie_breaker() -> None:
    policy = FinancialBlastRadiusSeverityPolicy(
        low_threshold=Decimal("10000"),
        medium_threshold=Decimal("50000"),
        high_threshold=Decimal("100000"),
        critical_threshold=Decimal("500000"),
    )

    first = FinancialExposure(
        field="balance",
        amount=Decimal("60000"),
        currency="INR",
    )
    second = FinancialExposure(
        field="income",
        amount=Decimal("60000"),
        currency="INR",
    )

    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (second, first),
    )

    assert result.ranked_exposures(policy) == (
        first,
        second,
    )


def test_ranked_exposures_never_compare_different_currencies() -> None:
    policy = FinancialBlastRadiusSeverityPolicy(
        low_threshold=Decimal("10000"),
        medium_threshold=Decimal("50000"),
        high_threshold=Decimal("100000"),
        critical_threshold=Decimal("500000"),
    )

    usd = FinancialExposure(
        field="usd_exposure",
        amount=Decimal("500000"),
        currency="USD",
    )
    inr = FinancialExposure(
        field="inr_exposure",
        amount=Decimal("10000"),
        currency="INR",
    )

    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (usd, inr),
    )

    ranked = result.ranked_exposures(policy)

    assert tuple(exposure.currency for exposure in ranked) == (
        "INR",
        "USD",
    )


def test_ranked_exposures_are_deterministic() -> None:
    policy = FinancialBlastRadiusSeverityPolicy(
        low_threshold=Decimal("10000"),
        medium_threshold=Decimal("50000"),
        high_threshold=Decimal("100000"),
        critical_threshold=Decimal("500000"),
    )

    first = FinancialExposure(
        field="income",
        amount=Decimal("60000"),
        currency="INR",
    )
    second = FinancialExposure(
        field="balance",
        amount=Decimal("60000"),
        currency="INR",
    )

    result = FinancialBlastRadius.from_exposures(
        uuid4(),
        (first, second),
    )

    first_ranking = result.ranked_exposures(policy)
    second_ranking = result.ranked_exposures(policy)

    assert first_ranking == second_ranking
