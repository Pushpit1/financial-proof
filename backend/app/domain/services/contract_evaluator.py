from app.domain.models.financial import FinancialContract
from app.domain.services.contract_evaluation import (
    ContractEvaluationResult,
    ContractViolation,
)
from app.domain.services.contract_validator import ContractValidator


class ContractEvaluator:
    """Deterministically evaluates the structural validity of a contract."""

    def __init__(
        self,
        validator: ContractValidator | None = None,
    ) -> None:
        self._validator = validator or ContractValidator()

    def evaluate(
        self,
        contract: FinancialContract,
    ) -> ContractEvaluationResult:
        validation = self._validator.validate(contract)

        violations = tuple(
            ContractViolation(
                rule="contract_validation",
                message=error,
            )
            for error in validation.errors
        )

        return ContractEvaluationResult(
            contract_id=contract.id,
            passed=validation.valid,
            violations=violations,
        )
