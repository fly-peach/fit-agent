"""add agent events table

Revision ID: 9a1c2f8a7b6d
Revises: 3f21a8b74d10
Create Date: 2026-04-15 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a1c2f8a7b6d"
down_revision: Union[str, Sequence[str], None] = "3f21a8b74d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 表已存在，跳过创建
    pass


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_events_user_id"), table_name="agent_events")
    op.drop_index(op.f("ix_agent_events_session_id"), table_name="agent_events")
    op.drop_index(op.f("ix_agent_events_sequence_number"), table_name="agent_events")
    op.drop_index(op.f("ix_agent_events_run_id"), table_name="agent_events")
    op.drop_index(op.f("ix_agent_events_event_type"), table_name="agent_events")
    op.drop_table("agent_events")
