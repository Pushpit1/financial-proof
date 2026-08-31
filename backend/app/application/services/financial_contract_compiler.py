"""Application service for natural-language financial contract compilation."""

from app.application.ports.financial_contract_compiler import (
    ContractCompilationResult,
    FinancialContractCompilerPort,
)
from app.application.ports.unit_of_work import FinancialUnitOfWorkPort
from app.domain.services.contract_validator import ContractValidator
from app.domain.value_objects.financial import ContractSourceText


class FinancialContractCompilerService:
    """Coordinate contract compilation, validation, and persistence."""

    def __init__(
        self,
        compiler: FinancialContractCompilerPort,
        validator: ContractValidator | None = None,
        unit_of_work: FinancialUnitOfWorkPort | None = None,
    ) -> None:
        self._compiler = compiler
        self._validator = validator or ContractValidator()
        self._unit_of_work = unit_of_work

    def compile(
        self,
        source_text: ContractSourceText,
    ) -> ContractCompilationResult:
        """Compile and validate a financial contract."""
        result = self._compiler.compile(source_text)

        if not isinstance(result, ContractCompilationResult):
            raise TypeError(
                "Compiler must return ContractCompilationResult."
            )

        validation = self._validator.validate(result.contract)

        if not validation.valid:
            raise ValueError(
                "Compiled financial contract is invalid: "
                + "; ".join(validation.errors)
            )

        return result

    def compile_and_persist(
        self,
        source_text: ContractSourceText,
    ) -> ContractCompilationResult:
        """Compile, validate, and persist a financial contract."""
        if self._unit_of_work is None:
            raise ValueError(
                "Compiler unit of work is required"
            )

        result = self.compile(source_text)

        with self._unit_of_work as unit_of_work:
            persisted_contract = unit_of_work.contracts.add(
                result.contract
            )

        return ContractCompilationResult(
            contract=persisted_contract,
            source_text=result.source_text,
        )
