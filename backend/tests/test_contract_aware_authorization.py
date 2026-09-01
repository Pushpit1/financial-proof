import pytest

from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.contract_authorization import (
    ContractAuthorizationRequest,
    FinancialOperation,
)
from app.domain.services.contract_aware_authorization_guard import (
    ContractAwareAuthorizationGuard,
)


def test_authorized_actor_and_operation_are_allowed() -> None:
    result = ContractAwareAuthorizationGuard().evaluate(
        ContractAuthorizationRequest(
            actor_id="operator-001",
            operation=FinancialOperation.REFUND,
            actor_authorized=True,
            operation_authorized=True,
        )
    )

    assert result[0] is GuardianDecision.ALLOW


def test_unauthorized_actor_is_blocked() -> None:
    result = ContractAwareAuthorizationGuard().evaluate(
        ContractAuthorizationRequest(
            actor_id="operator-001",
            operation=FinancialOperation.REFUND,
            actor_authorized=False,
            operation_authorized=True,
        )
    )

    assert result[0] is GuardianDecision.BLOCK
    assert "Actor is not authorized" in result[1]


def test_contract_forbidden_operation_is_blocked() -> None:
    result = ContractAwareAuthorizationGuard().evaluate(
        ContractAuthorizationRequest(
            actor_id="operator-001",
            operation=FinancialOperation.REFUND,
            actor_authorized=True,
            operation_authorized=False,
        )
    )

    assert result[0] is GuardianDecision.BLOCK
    assert "not authorized by the financial contract" in result[1]


def test_actor_authorization_does_not_override_contract() -> None:
    result = ContractAwareAuthorizationGuard().evaluate(
        ContractAuthorizationRequest(
            actor_id="operator-001",
            operation=FinancialOperation.CHARGE,
            actor_authorized=True,
            operation_authorized=False,
        )
    )

    assert result[0] is GuardianDecision.BLOCK


def test_empty_actor_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="Actor ID cannot be empty"):
        ContractAuthorizationRequest(
            actor_id="   ",
            operation=FinancialOperation.REFUND,
            actor_authorized=True,
            operation_authorized=True,
        )


def test_financial_operations_are_explicit() -> None:
    assert FinancialOperation.REFUND.value == "refund"
    assert FinancialOperation.CHARGE.value == "charge"
    assert FinancialOperation.FULFILLMENT.value == "fulfillment"


def test_contract_authorization_request_is_immutable() -> None:
    request = ContractAuthorizationRequest(
        actor_id="operator-001",
        operation=FinancialOperation.REFUND,
        actor_authorized=True,
        operation_authorized=True,
    )

    with pytest.raises(AttributeError):
        request.actor_authorized = False
