"""add meal breakdown to daily_nutrition

Revision ID: a1b2c3d4e5f6
Revises: e2c3ad11c3db
Create Date: 2026-04-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e2c3ad11c3db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for meal in ("breakfast", "lunch", "dinner"):
        op.add_column(
            "daily_nutritions",
            sa.Column(f"{meal}_calories_kcal", sa.Float, nullable=False, server_default="0"),
        )
        op.add_column(
            "daily_nutritions",
            sa.Column(f"{meal}_protein_g", sa.Float, nullable=False, server_default="0"),
        )
        op.add_column(
            "daily_nutritions",
            sa.Column(f"{meal}_carb_g", sa.Float, nullable=False, server_default="0"),
        )
        op.add_column(
            "daily_nutritions",
            sa.Column(f"{meal}_fat_g", sa.Float, nullable=False, server_default="0"),
        )


def downgrade() -> None:
    for meal in ("breakfast", "lunch", "dinner"):
        op.drop_column("daily_nutritions", f"{meal}_fat_g")
        op.drop_column("daily_nutritions", f"{meal}_carb_g")
        op.drop_column("daily_nutritions", f"{meal}_protein_g")
        op.drop_column("daily_nutritions", f"{meal}_calories_kcal")
