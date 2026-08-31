from decimal import Decimal
from uuid import uuid4

from app.domain.enums.financial import (
    ClaimType,
    ContractOperator,
)
from app.domain.models.financial import FinancialContract
from app.domain.services.contract_evaluator import ContractEvaluator
from app.domain.value_objects.financial import (
    ContractField,
    FinancialConstraint,
)


def test_evaluator_passes_valid_contract() -> None:
    contract = FinancialContract(
        name="Income Verification",
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

    result = ContractEvaluator().evaluate(contract)

    assert result.contract_id == contract.id
    assert result.passed is True
    assert result.violations == ()
    assert result.violation_count == 0


def test_evaluator_returns_contract_id() -> None:
    contract_id = uuid4()

    contract = object.__new__(FinancialContract)

    object.__setattr__(contract, "id", contract_id)
    object.__setattr__(contract, "name", "Test Contract")
    object.__setattr__(contract, "version", 1)
    object.__setattr__(contract, "minimum_confidence", None)
    object.__setattr__(
        contract,
        "minimum_supported_claim_ratio",
        Decimal("1"),
    )
    object.__setattr__(contract, "required_claim_types", ())
    object.__setattr__(contract, "preconditions", ())
    object.__setattr__(contract, "invariants", ())
    object.__setattr__(contract, "postconditions", ())
    object.__setattr__(contract, "inputs", ())
    object.__setattr__(contract, "outputs", ())
    object.__setattr__(contract, "financial_constraints", ())
    object.__setattr__(contract, "authorizations", ())
    object.__setattr__(contract, "temporal_rules", ())
    object.__setattr__(contract, "idempotency_policy", None)
    object.__setattr__(contract, "state_transitions", ())

    result = ContractEvaluator().evaluate(contract)

    assert result.contract_id == contract_id
    assert result.passed is True


def test_evaluator_converts_validation_errors_to_violations() -> None:
    contract = object.__new__(FinancialContract)

    object.__setattr__(contract, "id", uuid4())
    object.__setattr__(contract, "name", "Invalid Contract")
    object.__setattr__(contract, "version", 1)
    object.__setattr__(contract, "minimum_confidence", None)
    object.__setattr__(
        contract,
        "minimum_supported_claim_ratio",
        Decimal("1"),
    )
    object.__setattr__(
        contract,
        "required_claim_types",
        (ClaimType.INCOME, ClaimType.INCOME),
    )
    object.__setattr__(contract, "preconditions", ())
    object.__setattr__(contract, "invariants", ())
    object.__setattr__(contract, "postconditions", ())
    object.__setattr__(contract, "inputs", ())
    object.__setattr__(contract, "outputs", ())
    object.__setattr__(contract, "financial_constraints", ())
    object.__setattr__(contract, "authorizations", ())
    object.__setattr__(contract, "temporal_rules", ())
    object.__setattr__(contract, "idempotency_policy", None)
    object.__setattr__(contract, "state_transitions", ())

    result = ContractEvaluator().evaluate(contract)

    assert result.passed is False
    assert result.violation_count == 1
    assert result.violations[0].rule == "contract_validation"
    assert (
        result.violations[0].message
        == "Duplicate required claim type: 'income'."
    )


def test_evaluator_uses_injected_validator() -> None:
    class FakeValidator:
        def validate(self, contract: FinancialContract):
            from app.domain.services.contract_validator import (
                ContractValidationResult,
            )

            return ContractValidationResult(
                valid=False,
                errors=("Injected validation failure.",),
            )

    contract = FinancialContract(
        name="Injected Validator Contract",
    )

    result = ContractEvaluator(
        validator=FakeValidator()
    ).evaluate(contract)

    assert result.passed is False
    assert result.violation_count == 1
    assert (
        result.violations[0].message
        == "Injected validation failure."
    )
