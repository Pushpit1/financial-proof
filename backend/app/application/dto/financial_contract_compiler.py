"""Structured output models for financial contract compilation."""

from dataclasses import dataclass
from typing import Any

from app.domain.models.financial import FinancialContract


@dataclass(frozen=True)
class CompiledContractData:
    """Structured contract data produced by a compiler."""

    name: str
    fields: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate compiler output before domain construction."""
        if not isinstance(self.name, str):
            raise TypeError("Compiled contract name must be a string.")

        if not self.name.strip():
            raise ValueError("Compiled contract name cannot be empty.")

        if not isinstance(self.fields, dict):
            raise TypeError("Compiled contract fields must be a dictionary.")

        allowed_fields = {
            field_name
            for field_name in FinancialContract.__dataclass_fields__
            if field_name not in {"id", "name"}
        }

        unknown_fields = set(self.fields) - allowed_fields

        if unknown_fields:
            raise ValueError(
                "Unknown compiled contract fields: "
                + ", ".join(sorted(unknown_fields))
            )

    def to_domain_contract(self) -> FinancialContract:
        """Convert validated compiler output into a domain contract."""
        return FinancialContract(
            name=self.name,
            **self.fields,
        )
