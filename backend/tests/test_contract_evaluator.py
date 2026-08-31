from decimal import Decimal

from app.domain.enums.financial import (
    ClaimType,
    ContractOperator,
    ContractRuleType,
)
from app.domain.models.financial import FinancialContract
from app.domain.services.contract_evaluator import ContractEvaluator
from app.domain.value_objects.financial import (
    ContractCondition,
    ContractField,
    ContractRule,
    FinancialConstraint,
)


def make_contract(
    rule: ContractRule | None = None,
    constraint: FinancialConstraint | None = None,
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
            constraint
            if constraint is not None
            else FinancialConstraint(
                field="monthly_income",
                operator=ContractOperator.GREATER_THAN_OR_EQUAL,
                value=Decimal("50000"),
                currency="INR",
            ),
        ),
        invariants=(rule,) if rule else (),
    )


def test_evaluator_passes_valid_contract() -> None:
    contract = make_contract()

    result = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("75000")},
    )

    assert result.contract_id == contract.id
    assert result.passed is True
    assert result.violations == ()


def test_evaluator_equals_condition() -> None:
    rule = ContractRule(
        name="employment_status",
        condition=ContractCondition(
            field="employment_status",
            operator=ContractOperator.EQUALS,
            value="employed",
        ),
        rule_type=ContractRuleType.INVARIANT,
    )

    contract = make_contract(rule)

    result = ContractEvaluator().evaluate(
        contract,
        {
            "monthly_income": Decimal("75000"),
            "employment_status": "employed",
        },
    )

    assert result.passed is True


def test_evaluator_rejects_failed_equals_condition() -> None:
    rule = ContractRule(
        name="employment_status",
        condition=ContractCondition(
            field="employment_status",
            operator=ContractOperator.EQUALS,
            value="employed",
        ),
        rule_type=ContractRuleType.INVARIANT,
    )

    contract = make_contract(rule)

    result = ContractEvaluator().evaluate(
        contract,
        {
            "monthly_income": Decimal("75000"),
            "employment_status": "unemployed",
        },
    )

    assert result.passed is False
    assert result.violation_count == 1
    assert result.violations[0].rule == "employment_status"
    assert result.violations[0].field == "employment_status"


def test_financial_constraint_passes() -> None:
    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.GREATER_THAN_OR_EQUAL,
        value=Decimal("50000"),
        currency="INR",
    )

    contract = make_contract(constraint=constraint)

    result = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("50000")},
    )

    assert result.passed is True
    assert result.violations == ()


def test_financial_constraint_rejects_below_minimum() -> None:
    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.GREATER_THAN_OR_EQUAL,
        value=Decimal("50000"),
        currency="INR",
    )

    contract = make_contract(constraint=constraint)

    result = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("49999")},
    )

    assert result.passed is False
    assert result.violation_count == 1
    assert result.violations[0].rule == "financial_constraint"
    assert result.violations[0].field == "monthly_income"


def test_missing_financial_constraint_field_fails() -> None:
    contract = make_contract()

    result = ContractEvaluator().evaluate(contract, {})

    assert result.passed is False
    assert result.violation_count == 1
    assert result.violations[0].rule == "financial_constraint"


def test_financial_constraint_less_than_passes() -> None:
    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.LESS_THAN,
        value=Decimal("100000"),
        currency="INR",
    )

    contract = make_contract(constraint=constraint)

    result = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("75000")},
    )

    assert result.passed is True


def test_financial_constraint_less_than_or_equal_passes() -> None:
    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.LESS_THAN_OR_EQUAL,
        value=Decimal("75000"),
        currency="INR",
    )

    contract = make_contract(constraint=constraint)

    result = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("75000")},
    )

    assert result.passed is True


def test_financial_constraint_equals_passes() -> None:
    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.EQUALS,
        value=Decimal("75000"),
        currency="INR",
    )

    contract = make_contract(constraint=constraint)

    result = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("75000")},
    )

    assert result.passed is True


def test_financial_constraint_not_equals_passes() -> None:
    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.NOT_EQUALS,
        value=Decimal("75000"),
        currency="INR",
    )

    contract = make_contract(constraint=constraint)

    result = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("80000")},
    )

    assert result.passed is True


def test_condition_and_financial_constraint_both_evaluate() -> None:
    rule = ContractRule(
        name="employment_status",
        condition=ContractCondition(
            field="employment_status",
            operator=ContractOperator.EQUALS,
            value="employed",
        ),
        rule_type=ContractRuleType.INVARIANT,
    )

    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.GREATER_THAN_OR_EQUAL,
        value=Decimal("50000"),
        currency="INR",
    )

    contract = make_contract(
        rule=rule,
        constraint=constraint,
    )

    result = ContractEvaluator().evaluate(
        contract,
        {
            "monthly_income": Decimal("75000"),
            "employment_status": "employed",
        },
    )

    assert result.passed is True
    assert result.violations == ()
