"""add proof evaluation history

Revision ID: 4d1a2b3c4e5f
Revises: 3c092bcf4ce5
Create Date: 2026-08-29 21:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4d1a2b3c4e5f"
down_revision: str | Sequence[str] | None = "3c092bcf4ce5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create proof evaluation history table."""
    op.create_table(
        "proof_evaluations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("proof_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "overall_confidence",
            sa.Numeric(5, 4),
            nullable=False,
        ),
        sa.Column(
            "evaluation_reasons",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_proof_evaluations_proof_id",
        "proof_evaluations",
        ["proof_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop proof evaluation history table."""
    op.drop_index(
        "ix_proof_evaluations_proof_id",
        table_name="proof_evaluations",
    )
    op.drop_table("proof_evaluations")
