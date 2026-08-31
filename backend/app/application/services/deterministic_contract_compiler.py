"""Deterministic financial contract compiler."""

from app.application.dto.financial_contract_compiler import (
    CompiledContractData,
)
from app.application.ports.financial_contract_compiler import (
    ContractCompilationResult,
    FinancialContractCompilerPort,
)
from app.domain.value_objects.financial import ContractSourceText


class DeterministicFinancialContractCompiler(
    FinancialContractCompilerPort,
):
    """Compile a small deterministic contract representation."""

    def compile(
        self,
        source_text: ContractSourceText,
    ) -> ContractCompilationResult:
        """Compile source text into a basic financial contract."""
        normalized_source = source_text.normalized()

        data = CompiledContractData(
            name=self._derive_contract_name(normalized_source),
            fields={},
        )

        return ContractCompilationResult(
            contract=data.to_domain_contract(),
            source_text=source_text,
        )

    @staticmethod
    def _derive_contract_name(source_text: str) -> str:
        """Derive a stable contract name from source text."""
        first_line = source_text.splitlines()[0].strip()

        if len(first_line) <= 80:
            return first_line

        return first_line[:77].rstrip() + "..."
