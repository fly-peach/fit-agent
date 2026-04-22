"""remove coach_id from assessments

Revision ID: 61666276a931
Revises: 65b09800e46a
Create Date: 2026-04-14 22:47:41.528680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61666276a931'
down_revision: Union[str, Sequence[str], None] = '65b09800e46a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("assessments", recreate="always") as batch_op:
        batch_op.drop_index("ix_assessments_coach_id")
        batch_op.drop_column("coach_id")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("assessments", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("coach_id", sa.Integer(), nullable=False))
        batch_op.create_foreign_key("fk_assessments_coach_id_users", "users", ["coach_id"], ["id"])
        batch_op.create_index("ix_assessments_coach_id", ["coach_id"], unique=False)
