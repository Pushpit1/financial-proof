"""Tests for the financial contract compiler application port."""

import pytest

from app.application.ports.financial_contract_compiler import (
    ContractCompilationResult,
    FinancialContractCompilerPort,
)
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import ContractSourceText


class FakeCompiler(FinancialContractCompilerPort):
    """Test compiler implementation."""

    def compile(
        self,
        source_text: ContractSourceText,
    ) -> ContractCompilationResult:
        return ContractCompilationResult(
            contract=FinancialContract(
                name="Compiled Contract",
            ),
            source_text=source_text,
        )


def test_contract_source_text_accepts_valid_text() -> None:
    source = ContractSourceText(
        "Customer may receive a refund within 30 days."
    )

    assert source.value == (
        "Customer may receive a refund within 30 days."
    )


def test_contract_source_text_normalizes_whitespace() -> None:
    source = ContractSourceText(
        "   Customer may receive a refund.   "
    )

    assert source.normalized() == (
        "Customer may receive a refund."
    )


@pytest.mark.parametrize(
    "source_text",
    [
        "",
        "   ",
        "\n\t",
    ],
)
def test_contract_source_text_rejects_empty_text(
    source_text: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="Contract source text cannot be empty",
    ):
        ContractSourceText(source_text)


def test_compiler_returns_structured_contract_result() -> None:
    compiler = FakeCompiler()
    source = ContractSourceText(
        "Customer may receive a refund within 30 days."
    )

    result = compiler.compile(source)

    assert isinstance(result, ContractCompilationResult)
    assert isinstance(result.contract, FinancialContract)
    assert result.source_text == source


def test_compilation_result_is_immutable() -> None:
    result = ContractCompilationResult(
        contract=FinancialContract(name="Immutable Contract"),
        source_text=ContractSourceText(
            "A customer may request a refund."
        ),
    )

    with pytest.raises(AttributeError):
        result.source_text = ContractSourceText("changed")  # type: ignore[misc]
