"""Dependency providers for financial contract compilation."""


from app.application.services.deterministic_contract_compiler import (
    DeterministicFinancialContractCompiler,
)
from app.application.services.financial_contract_compiler import (
    FinancialContractCompilerService,
)


def get_financial_contract_compiler_service() -> FinancialContractCompilerService:
    """Build the natural-language financial contract compiler service."""
    return FinancialContractCompilerService(
        compiler=DeterministicFinancialContractCompiler(),
    )
