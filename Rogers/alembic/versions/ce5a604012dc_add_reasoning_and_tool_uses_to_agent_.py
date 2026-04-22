"""add_reasoning_and_tool_uses_to_agent_messages

Revision ID: ce5a604012dc
Revises: 9a1c2f8a7b6d
Create Date: 2026-04-20 13:49:01.726702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce5a604012dc'
down_revision: Union[str, Sequence[str], None] = '9a1c2f8a7b6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 reasoning 列
    op.add_column('agent_messages', sa.Column('reasoning', sa.Text(), nullable=True))
    # 添加 tool_uses 列（JSON 类型）
    op.add_column('agent_messages', sa.Column('tool_uses', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # 删除 tool_uses 列
    op.drop_column('agent_messages', 'tool_uses')
    # 删除 reasoning 列
    op.drop_column('agent_messages', 'reasoning')
