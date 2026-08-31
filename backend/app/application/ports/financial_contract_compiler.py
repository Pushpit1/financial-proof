"""Application port for natural-language financial contract compilation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import ContractSourceText


@dataclass(frozen=True)
class ContractCompilationResult:
    """Structured result produced by a contract compiler."""

    contract: FinancialContract
    source_text: ContractSourceText


class FinancialContractCompilerPort(ABC):
    """Application boundary for natural-language contract compilation."""

    @abstractmethod
    def compile(
        self,
        source_text: ContractSourceText,
    ) -> ContractCompilationResult:
        """Compile natural-language contract rules into a domain contract."""
        raise NotImplementedError
