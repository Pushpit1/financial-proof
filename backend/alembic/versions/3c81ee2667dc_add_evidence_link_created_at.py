"""add evidence link created at

Revision ID: 3c81ee2667dc
Revises: 0854158e4256
Create Date: 2026-08-30 22:25:35.819615

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3c81ee2667dc"
down_revision: str | Sequence[str] | None = "0854158e4256"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add creation timestamp to evidence links."""
    op.add_column(
        "evidence_links",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.alter_column(
        "evidence_links",
        "created_at",
        server_default=None,
    )


def downgrade() -> None:
    """Remove creation timestamp from evidence links."""
    op.drop_column(
        "evidence_links",
        "created_at",
    )