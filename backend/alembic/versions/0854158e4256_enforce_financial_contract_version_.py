"""enforce financial contract version uniqueness

Revision ID: 0854158e4256
Revises: 1d64cfe5b58b
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0854158e4256"
down_revision: str | Sequence[str] | None = "1d64cfe5b58b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add uniqueness constraint for contract name and version."""
    op.create_unique_constraint(
        "uq_financial_contract_name_version",
        "financial_contracts",
        ["name", "version"],
    )


def downgrade() -> None:
    """Remove uniqueness constraint for contract name and version."""
    op.drop_constraint(
        "uq_financial_contract_name_version",
        "financial_contracts",
        type_="unique",
    )
