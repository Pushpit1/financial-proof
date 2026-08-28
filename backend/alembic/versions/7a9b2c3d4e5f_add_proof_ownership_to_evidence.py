"""add proof ownership to evidence

Revision ID: 7a9b2c3d4e5f
Revises: 4e3e28398ddf
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7a9b2c3d4e5f"
down_revision: str | Sequence[str] | None = "4e3e28398ddf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evidence",
        sa.Column(
            "proof_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_evidence_proof_id",
        "evidence",
        "financial_proofs",
        ["proof_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_evidence_proof_id",
        "evidence",
        type_="foreignkey",
    )

    op.drop_column("evidence", "proof_id")
