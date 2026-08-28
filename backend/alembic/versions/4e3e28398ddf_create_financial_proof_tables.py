"""create financial proof tables

Revision ID: 4e3e28398ddf
Revises: 5e3161c065ab
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "4e3e28398ddf"
down_revision: str | Sequence[str] | None = "5e3161c065ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_proofs",
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "overall_confidence",
            sa.Numeric(precision=5, scale=4),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "financial_claims",
        sa.Column("claim_type", sa.String(length=50), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column(
            "amount",
            sa.Numeric(precision=20, scale=2),
            nullable=True,
        ),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "confidence",
            sa.Numeric(precision=5, scale=4),
            nullable=False,
        ),
        sa.Column(
            "confidence_level",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("proof_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["proof_id"],
            ["financial_proofs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evidence",
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("received_at", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("checksum", sa.String(length=255), nullable=True),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evidence_links",
        sa.Column("claim_id", sa.UUID(), nullable=False),
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column(
            "verification_status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "confidence",
            sa.Numeric(precision=5, scale=4),
            nullable=False,
        ),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["financial_claims.id"],
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("evidence_links")
    op.drop_table("evidence")
    op.drop_table("financial_claims")
    op.drop_table("financial_proofs")
