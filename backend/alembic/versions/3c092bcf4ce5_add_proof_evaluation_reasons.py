"""add proof evaluation reasons

Revision ID: 3c092bcf4ce5
Revises: 7a9b2c3d4e5f
Create Date: 2026-08-29 21:11:16.012759

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c092bcf4ce5"
down_revision: str | Sequence[str] | None = "7a9b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add persisted proof evaluation reasons."""
    op.add_column(
        "financial_proofs",
        sa.Column(
            "evaluation_reasons",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )


def downgrade() -> None:
    """Remove persisted proof evaluation reasons."""
    op.drop_column(
        "financial_proofs",
        "evaluation_reasons",
    )
