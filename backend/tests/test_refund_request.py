import pytest

from app.domain.models.refund_request import RefundRequest


def test_refund_request_is_created() -> None:
    request = RefundRequest(
        amount_minor=5000,
        currency="INR",
        approval_granted=True,
    )

    assert request.amount_minor == 5000
    assert request.currency == "INR"
    assert request.approval_granted is True


def test_refund_request_defaults_to_not_approved() -> None:
    request = RefundRequest(
        amount_minor=5000,
        currency="INR",
    )

    assert request.approval_granted is False


@pytest.mark.parametrize(
    "amount",
    [0, -1, -5000],
)
def test_refund_amount_must_be_positive(amount: int) -> None:
    with pytest.raises(ValueError, match="Refund amount must be positive"):
        RefundRequest(
            amount_minor=amount,
            currency="INR",
        )


def test_refund_currency_must_be_three_letters() -> None:
    with pytest.raises(
        ValueError,
        match="Refund currency must be a 3-letter code",
    ):
        RefundRequest(
            amount_minor=5000,
            currency="IN",
        )


def test_refund_request_is_immutable() -> None:
    request = RefundRequest(
        amount_minor=5000,
        currency="INR",
    )

    with pytest.raises(AttributeError):
        request.amount_minor = 10000
