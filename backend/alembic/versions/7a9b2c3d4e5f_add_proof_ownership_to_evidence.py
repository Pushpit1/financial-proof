from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7a9b2c3d4e5f"
down_revision: str | Sequence[str] | None = "4e3e28398ddf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("evidence") as batch_op:
        batch_op.add_column(
            sa.Column(
                "proof_id",
                sa.UUID(),
                nullable=True,
            ),
        )
        batch_op.create_foreign_key(
            "fk_evidence_proof_id",
            "financial_proofs",
            ["proof_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("evidence") as batch_op:
        batch_op.drop_constraint(
            "fk_evidence_proof_id",
            type_="foreignkey",
        )
        batch_op.drop_column("proof_id")
