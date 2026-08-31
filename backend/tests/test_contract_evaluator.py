from datetime import UTC, datetime

from app.domain.enums.financial import (
    ClaimType,
    ContractAuthorizationAction,
    ContractOperator,
    ContractRuleType,
    ContractTimeRelation,
)
from app.domain.models.financial import FinancialContract
from app.domain.services.contract_evaluator import ContractEvaluator
from app.domain.value_objects.financial import (
    ContractAuthorization,
    ContractCondition,
    ContractField,
    ContractRule,
    ContractTemporalRule,
    FinancialConstraint,
)


def make_contract(
    rule: ContractRule | None = None,
) -> FinancialContract:
    return FinancialContract(
        name="Income Verification",
        version=1,
        required_claim_types=(ClaimType.INCOME,),
        inputs=(
            ContractField(
                name="monthly_income",
                data_type="decimal",
            ),
        ),
        financial_constraints=(
            FinancialConstraint(
                field="monthly_income",
                operator=ContractOperator.GREATER_THAN_OR_EQUAL,
                value=50000,
                currency="INR",
            ),
        ),
        invariants=(rule,) if rule else (),
    )


def test_authorization_passes_for_matching_context() -> None:
    contract = FinancialContract(
        name="Authorized Contract",
        authorizations=(
            ContractAuthorization(
                actor="underwriter",
                action=ContractAuthorizationAction.EVALUATE,
                resource="financial_proof",
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "actor": "underwriter",
            "action": "evaluate",
            "resource": "financial_proof",
        },
    )

    assert result.passed is True


def test_authorization_rejects_wrong_actor() -> None:
    contract = FinancialContract(
        name="Authorized Contract",
        authorizations=(
            ContractAuthorization(
                actor="underwriter",
                action=ContractAuthorizationAction.EVALUATE,
                resource="financial_proof",
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "actor": "auditor",
            "action": "evaluate",
            "resource": "financial_proof",
        },
    )

    assert result.passed is False
    assert result.violations[0].rule == "authorization"
    assert result.violations[0].field == "actor"


def test_authorization_rejects_wrong_action() -> None:
    contract = FinancialContract(
        name="Authorized Contract",
        authorizations=(
            ContractAuthorization(
                actor="underwriter",
                action=ContractAuthorizationAction.APPROVE,
                resource="financial_proof",
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "actor": "underwriter",
            "action": "evaluate",
            "resource": "financial_proof",
        },
    )

    assert result.passed is False
    assert result.violations[0].rule == "authorization"


def test_authorization_rejects_wrong_resource() -> None:
    contract = FinancialContract(
        name="Authorized Contract",
        authorizations=(
            ContractAuthorization(
                actor="underwriter",
                action=ContractAuthorizationAction.EVALUATE,
                resource="financial_proof",
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "actor": "underwriter",
            "action": "evaluate",
            "resource": "other_resource",
        },
    )

    assert result.passed is False


def test_temporal_rule_on_or_after_passes() -> None:
    contract = FinancialContract(
        name="Temporal Contract",
        temporal_rules=(
            ContractTemporalRule(
                field="created_at",
                relation=ContractTimeRelation.ON_OR_AFTER,
                start=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "created_at": datetime(
                2026,
                6,
                1,
                tzinfo=UTC,
            ),
        },
    )

    assert result.passed is True


def test_temporal_rule_rejects_before_boundary() -> None:
    contract = FinancialContract(
        name="Temporal Contract",
        temporal_rules=(
            ContractTemporalRule(
                field="created_at",
                relation=ContractTimeRelation.ON_OR_AFTER,
                start=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "created_at": datetime(
                2025,
                12,
                31,
                tzinfo=UTC,
            ),
        },
    )

    assert result.passed is False
    assert result.violations[0].rule == "temporal_rule"


def test_temporal_between_passes() -> None:
    contract = FinancialContract(
        name="Temporal Contract",
        temporal_rules=(
            ContractTemporalRule(
                field="created_at",
                relation=ContractTimeRelation.BETWEEN,
                start=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=UTC,
                ),
                end=datetime(
                    2026,
                    12,
                    31,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "created_at": datetime(
                2026,
                6,
                1,
                tzinfo=UTC,
            ),
        },
    )

    assert result.passed is True


def test_missing_temporal_context_fails() -> None:
    contract = FinancialContract(
        name="Temporal Contract",
        temporal_rules=(
            ContractTemporalRule(
                field="created_at",
                relation=ContractTimeRelation.ON_OR_AFTER,
                start=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    result = ContractEvaluator().evaluate(contract, {})

    assert result.passed is False
    assert result.violations[0].field == "created_at"


def test_condition_and_authorization_can_both_pass() -> None:
    rule = ContractRule(
        name="employment_status",
        condition=ContractCondition(
            field="employment_status",
            operator=ContractOperator.EQUALS,
            value="employed",
        ),
        rule_type=ContractRuleType.INVARIANT,
    )

    contract = FinancialContract(
        name="Combined Contract",
        invariants=(rule,),
        authorizations=(
            ContractAuthorization(
                actor="underwriter",
                action=ContractAuthorizationAction.EVALUATE,
                resource="financial_proof",
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "employment_status": "employed",
            "actor": "underwriter",
            "action": "evaluate",
            "resource": "financial_proof",
        },
    )

    assert result.passed is True

def test_evaluation_result_exposes_reason_codes() -> None:
    contract = FinancialContract(
        name="Reason Code Contract",
        authorizations=(
            ContractAuthorization(
                actor="underwriter",
                action=ContractAuthorizationAction.EVALUATE,
                resource="financial_proof",
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "actor": "auditor",
            "action": "evaluate",
            "resource": "financial_proof",
        },
    )

    assert result.passed is False
    assert result.reason_codes == ("authorization_failed",)


def test_condition_failure_has_deterministic_reason_code() -> None:
    rule = ContractRule(
        name="employment_status",
        condition=ContractCondition(
            field="employment_status",
            operator=ContractOperator.EQUALS,
            value="employed",
        ),
        rule_type=ContractRuleType.INVARIANT,
    )

    contract = FinancialContract(
        name="Condition Reason Contract",
        invariants=(rule,),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {"employment_status": "unemployed"},
    )

    assert result.passed is False
    assert result.reason_codes == ("invariant_failed",)


def test_temporal_failure_has_deterministic_reason_code() -> None:
    contract = FinancialContract(
        name="Temporal Reason Contract",
        temporal_rules=(
            ContractTemporalRule(
                field="created_at",
                relation=ContractTimeRelation.ON_OR_AFTER,
                start=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "created_at": datetime(
                2025,
                1,
                1,
                tzinfo=UTC,
            ),
        },
    )

    assert result.reason_codes == ("temporal_rule_failed",)


def test_missing_temporal_value_has_deterministic_reason_code() -> None:
    contract = FinancialContract(
        name="Temporal Missing Contract",
        temporal_rules=(
            ContractTemporalRule(
                field="created_at",
                relation=ContractTimeRelation.ON_OR_AFTER,
                start=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    result = ContractEvaluator().evaluate(contract, {})

    assert result.reason_codes == ("temporal_value_missing",)


def test_financial_constraint_failure_has_deterministic_reason_code() -> None:
    contract = FinancialContract(
        name="Financial Reason Contract",
        inputs=(
            ContractField(
                name="monthly_income",
                data_type="decimal",
            ),
        ),
        financial_constraints=(
            FinancialConstraint(
                field="monthly_income",
                operator=ContractOperator.GREATER_THAN_OR_EQUAL,
                value=50000,
                currency="INR",
            ),
        ),
    )

    result = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": 10000},
    )

    assert result.reason_codes == (
        "financial_constraint_failed",
    )
