"""remove role from users

Revision ID: e87c1dee3a2f
Revises: 61666276a931
Create Date: 2026-04-14 23:08:02.510314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e87c1dee3a2f'
down_revision: Union[str, Sequence[str], None] = '61666276a931'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("users", recreate="always") as batch_op:
        batch_op.drop_column("role")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("users", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(length=32), nullable=False, server_default="member"))
