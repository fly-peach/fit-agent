"""add daily tracking tables

Revision ID: 3f21a8b74d10
Revises: 0e43dad3048d
Create Date: 2026-04-15 11:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3f21a8b74d10"
down_revision: Union[str, Sequence[str], None] = "0e43dad3048d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 表已存在，跳过创建
    pass


def downgrade() -> None:
    op.drop_index(op.f("ix_daily_nutritions_user_id"), table_name="daily_nutritions")
    op.drop_index(op.f("ix_daily_nutritions_record_date"), table_name="daily_nutritions")
    op.drop_index(op.f("ix_daily_nutritions_id"), table_name="daily_nutritions")
    op.drop_table("daily_nutritions")

    op.drop_index(op.f("ix_daily_workout_plans_user_id"), table_name="daily_workout_plans")
    op.drop_index(op.f("ix_daily_workout_plans_record_date"), table_name="daily_workout_plans")
    op.drop_index(op.f("ix_daily_workout_plans_id"), table_name="daily_workout_plans")
    op.drop_table("daily_workout_plans")

    op.drop_index(op.f("ix_daily_metrics_user_id"), table_name="daily_metrics")
    op.drop_index(op.f("ix_daily_metrics_record_date"), table_name="daily_metrics")
    op.drop_index(op.f("ix_daily_metrics_id"), table_name="daily_metrics")
    op.drop_table("daily_metrics")
