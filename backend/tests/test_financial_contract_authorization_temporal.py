from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.enums.financial import (
    ContractAuthorizationAction,
    ContractOperator,
    ContractTimeRelation,
)
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import (
    ContractAuthorization,
    ContractField,
    ContractTemporalRule,
    FinancialConstraint,
)


def test_contract_authorization_is_immutable() -> None:
    authorization = ContractAuthorization(
        actor="underwriter",
        action=ContractAuthorizationAction.APPROVE,
        resource="financial_proof",
    )

    with pytest.raises(AttributeError):
        authorization.actor = "admin"  # type: ignore[misc]


def test_contract_authorization_supports_operation() -> None:
    authorization = ContractAuthorization(
        actor="underwriter",
        action=ContractAuthorizationAction.APPROVE,
        resource="financial_proof",
    )

    assert authorization.actor == "underwriter"
    assert authorization.action == ContractAuthorizationAction.APPROVE
    assert authorization.resource == "financial_proof"


def test_contract_authorization_rejects_empty_actor() -> None:
    with pytest.raises(
        ValueError,
        match="Contract authorization actor cannot be empty",
    ):
        ContractAuthorization(
            actor="",
            action=ContractAuthorizationAction.READ,
            resource="financial_proof",
        )


def test_contract_authorization_rejects_empty_resource() -> None:
    with pytest.raises(
        ValueError,
        match="Contract authorization resource cannot be empty",
    ):
        ContractAuthorization(
            actor="underwriter",
            action=ContractAuthorizationAction.READ,
            resource="",
        )


def test_temporal_rule_supports_between() -> None:
    start = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )
    end = datetime(
        2026,
        12,
        31,
        tzinfo=UTC,
    )

    rule = ContractTemporalRule(
        field="transaction.created_at",
        relation=ContractTimeRelation.BETWEEN,
        start=start,
        end=end,
    )

    assert rule.field == "transaction.created_at"
    assert rule.relation == ContractTimeRelation.BETWEEN
    assert rule.start == start
    assert rule.end == end


def test_temporal_rule_supports_single_boundary() -> None:
    start = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    rule = ContractTemporalRule(
        field="transaction.created_at",
        relation=ContractTimeRelation.ON_OR_AFTER,
        start=start,
    )

    assert rule.start == start
    assert rule.end is None


def test_temporal_rule_is_immutable() -> None:
    rule = ContractTemporalRule(
        field="transaction.created_at",
        relation=ContractTimeRelation.ON_OR_AFTER,
        start=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    with pytest.raises(AttributeError):
        rule.field = "changed"  # type: ignore[misc]


def test_temporal_rule_rejects_empty_field() -> None:
    with pytest.raises(
        ValueError,
        match="Contract temporal rule field cannot be empty",
    ):
        ContractTemporalRule(
            field="",
            relation=ContractTimeRelation.ON_OR_AFTER,
            start=datetime(
                2026,
                1,
                1,
                tzinfo=UTC,
            ),
        )


def test_between_temporal_rule_requires_end() -> None:
    with pytest.raises(
        ValueError,
        match="Between temporal rules require an end timestamp",
    ):
        ContractTemporalRule(
            field="transaction.created_at",
            relation=ContractTimeRelation.BETWEEN,
            start=datetime(
                2026,
                1,
                1,
                tzinfo=UTC,
            ),
        )


def test_between_temporal_rule_rejects_reversed_range() -> None:
    with pytest.raises(
        ValueError,
        match="Temporal rule end cannot precede its start",
    ):
        ContractTemporalRule(
            field="transaction.created_at",
            relation=ContractTimeRelation.BETWEEN,
            start=datetime(
                2026,
                12,
                31,
                tzinfo=UTC,
            ),
            end=datetime(
                2026,
                1,
                1,
                tzinfo=UTC,
            ),
        )


def test_non_between_temporal_rule_rejects_end() -> None:
    with pytest.raises(
        ValueError,
        match="Only between temporal rules may define an end timestamp",
    ):
        ContractTemporalRule(
            field="transaction.created_at",
            relation=ContractTimeRelation.AFTER,
            start=datetime(
                2026,
                1,
                1,
                tzinfo=UTC,
            ),
            end=datetime(
                2026,
                2,
                1,
                tzinfo=UTC,
            ),
        )


def test_contract_supports_authorization_and_temporal_rules() -> None:
    authorization = ContractAuthorization(
        actor="underwriter",
        action=ContractAuthorizationAction.EVALUATE,
        resource="financial_proof",
    )

    temporal_rule = ContractTemporalRule(
        field="income.period_end",
        relation=ContractTimeRelation.ON_OR_AFTER,
        start=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    contract = FinancialContract(
        name="Income Verification",
        inputs=(
            ContractField(
                name="income",
                data_type="money",
            ),
        ),
        authorizations=(authorization,),
        temporal_rules=(temporal_rule,),
    )

    assert contract.authorizations == (authorization,)
    assert contract.temporal_rules == (temporal_rule,)


def test_financial_constraint_still_supports_currency() -> None:
    constraint = FinancialConstraint(
        field="income",
        operator=ContractOperator.GREATER_THAN_OR_EQUAL,
        value=Decimal("50000"),
        currency="inr",
    )

    assert constraint.currency == "INR"
