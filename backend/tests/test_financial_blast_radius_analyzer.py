from decimal import Decimal

from app.domain.enums.financial import ClaimType, ContractOperator
from app.domain.models.financial import FinancialContract
from app.domain.models.financial_blast_radius import FinancialBlastRadius
from app.domain.services.contract_evaluator import ContractEvaluator
from app.domain.services.financial_blast_radius import (
    FinancialBlastRadiusAnalyzer,
)
from app.domain.value_objects.financial import (
    ContractField,
    FinancialConstraint,
)


def make_income_contract() -> FinancialContract:
    return FinancialContract(
        name="Income Blast Radius Contract",
        version=1,
        required_claim_types=(ClaimType.INCOME,),
        inputs=(
            ContractField(
                name="monthly_income",
                data_type="money",
            ),
        ),
        financial_constraints=(
            FinancialConstraint(
                field="monthly_income",
                operator=ContractOperator.GREATER_THAN_OR_EQUAL,
                value=Decimal("50000"),
                currency="INR",
            ),
        ),
    )


def test_failed_financial_constraint_creates_exposure() -> None:
    contract = make_income_contract()

    evaluation = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("10000")},
    )

    result = FinancialBlastRadiusAnalyzer.analyze(
        contract,
        evaluation,
        {"monthly_income": Decimal("10000")},
    )

    assert isinstance(result, FinancialBlastRadius)
    assert result.exposure_count == 1
    assert result.affected_fields == ("monthly_income",)
    assert result.total_exposure == Decimal("10000")
    assert result.total_exposure_by_currency == {
        "INR": Decimal("10000"),
    }


def test_passing_financial_constraint_creates_no_exposure() -> None:
    contract = make_income_contract()

    evaluation = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("75000")},
    )

    result = FinancialBlastRadiusAnalyzer.analyze(
        contract,
        evaluation,
        {"monthly_income": Decimal("75000")},
    )

    assert result.exposures == ()
    assert result.exposure_count == 0
    assert result.affected_fields == ()


def test_non_financial_violation_does_not_create_exposure() -> None:
    contract = FinancialContract(
        name="Condition Contract",
        version=1,
        inputs=(
            ContractField(
                name="monthly_income",
                data_type="money",
            ),
        ),
    )

    evaluation = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("10000")},
    )

    result = FinancialBlastRadiusAnalyzer.analyze(
        contract,
        evaluation,
        {"monthly_income": Decimal("10000")},
    )

    assert result.exposure_count == 0


def test_multiple_failed_financial_constraints_create_multiple_exposures() -> None:
    contract = FinancialContract(
        name="Multi Financial Contract",
        version=1,
        inputs=(
            ContractField(
                name="monthly_income",
                data_type="money",
            ),
            ContractField(
                name="monthly_expense",
                data_type="money",
            ),
        ),
        financial_constraints=(
            FinancialConstraint(
                field="monthly_income",
                operator=ContractOperator.GREATER_THAN_OR_EQUAL,
                value=Decimal("50000"),
                currency="INR",
            ),
            FinancialConstraint(
                field="monthly_expense",
                operator=ContractOperator.LESS_THAN_OR_EQUAL,
                value=Decimal("20000"),
                currency="INR",
            ),
        ),
    )

    context = {
        "monthly_income": Decimal("30000"),
        "monthly_expense": Decimal("40000"),
    }

    evaluation = ContractEvaluator().evaluate(
        contract,
        context,
    )

    result = FinancialBlastRadiusAnalyzer.analyze(
        contract,
        evaluation,
        context,
    )

    assert result.exposure_count == 2
    assert result.affected_fields == (
        "monthly_income",
        "monthly_expense",
    )
    assert result.total_exposure == Decimal("70000")


def test_analyzer_preserves_violation_identity() -> None:
    contract = make_income_contract()

    evaluation = ContractEvaluator().evaluate(
        contract,
        {"monthly_income": Decimal("10000")},
    )

    result = FinancialBlastRadiusAnalyzer.analyze(
        contract,
        evaluation,
        {"monthly_income": Decimal("10000")},
    )

    assert result.exposures[0].source_violation_id == evaluation.violations[0].id


def test_missing_context_does_not_create_fake_exposure() -> None:
    contract = make_income_contract()

    evaluation = ContractEvaluator().evaluate(
        contract,
        {},
    )

    result = FinancialBlastRadiusAnalyzer.analyze(
        contract,
        evaluation,
        {},
    )

    assert result.exposure_count == 0


def test_analysis_is_deterministic_for_same_evaluation() -> None:
    contract = make_income_contract()
    context = {"monthly_income": Decimal("10000")}

    first_evaluation = ContractEvaluator().evaluate(
        contract,
        context,
    )
    second_evaluation = ContractEvaluator().evaluate(
        contract,
        context,
    )

    first = FinancialBlastRadiusAnalyzer.analyze(
        contract,
        first_evaluation,
        context,
    )
    second = FinancialBlastRadiusAnalyzer.analyze(
        contract,
        second_evaluation,
        context,
    )

    assert first.affected_fields == second.affected_fields
    assert first.total_exposure_by_currency == second.total_exposure_by_currency
    assert first.exposure_count == second.exposure_count
