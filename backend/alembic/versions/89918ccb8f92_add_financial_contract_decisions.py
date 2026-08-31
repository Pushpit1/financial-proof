"""add financial contract decisions

Revision ID: 89918ccb8f92
Revises: 3c81ee2667dc
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "89918ccb8f92"
down_revision: str | Sequence[str] | None = "3c81ee2667dc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the financial contract decisions table."""
    op.create_table(
        "financial_contract_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("contract_id", sa.Uuid(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column(
            "violation_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["contract_id"],
            ["financial_contracts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_financial_contract_decisions_contract_id",
        "financial_contract_decisions",
        ["contract_id"],
    )


def downgrade() -> None:
    """Drop the financial contract decisions table."""
    op.drop_index(
        "ix_financial_contract_decisions_contract_id",
        table_name="financial_contract_decisions",
    )
    op.drop_table("financial_contract_decisions")
