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
    with op.batch_alter_table("financial_contracts") as batch_op:
        batch_op.create_unique_constraint(
            "uq_financial_contract_name_version",
            ["name", "version"],
        )


def downgrade() -> None:
    """Remove uniqueness constraint for contract name and version."""
    with op.batch_alter_table("financial_contracts") as batch_op:
        batch_op.drop_constraint(
            "uq_financial_contract_name_version",
            type_="unique",
        )
