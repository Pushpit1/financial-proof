"""add financial guardian audit persistence

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create financial guardian audit persistence."""
    op.create_table(
        "financial_guardian_audit_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "actor_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "operation",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "rule",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "decision",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_financial_guardian_audit_records_created_at",
        "financial_guardian_audit_records",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop financial guardian audit persistence."""
    op.drop_index(
        "ix_financial_guardian_audit_records_created_at",
        table_name="financial_guardian_audit_records",
    )
    op.drop_table("financial_guardian_audit_records")
