"""add financial blast radius persistence

Revision ID: a1b2c3d4e5f6
Revises: 89918ccb8f92
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "89918ccb8f92"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create financial blast-radius persistence tables."""
    op.create_table(
        "financial_blast_radius",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "financial_exposures",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("source_violation_id", sa.Uuid(), nullable=True),
        sa.Column("field", sa.String(length=255), nullable=True),
        sa.Column(
            "amount",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "direct_loss",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "duplicate_charge_exposure",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "duplicate_fulfillment_exposure",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "refund_exposure",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "unauthorized_action_exposure",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "actual_exposure",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "maximum_exposure",
            sa.Numeric(20, 2),
            nullable=False,
            server_default="0",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["financial_blast_radius.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_financial_exposures_analysis_id",
        "financial_exposures",
        ["analysis_id"],
    )

    op.create_index(
        "ix_financial_exposures_source_violation_id",
        "financial_exposures",
        ["source_violation_id"],
    )


def downgrade() -> None:
    """Drop financial blast-radius persistence tables."""
    op.drop_index(
        "ix_financial_exposures_source_violation_id",
        table_name="financial_exposures",
    )
    op.drop_index(
        "ix_financial_exposures_analysis_id",
        table_name="financial_exposures",
    )
    op.drop_table("financial_exposures")
    op.drop_table("financial_blast_radius")
