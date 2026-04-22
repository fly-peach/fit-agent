"""add body composition records

Revision ID: 0e43dad3048d
Revises: e87c1dee3a2f
Create Date: 2026-04-15 00:10:20.128672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '0e43dad3048d'
down_revision: Union[str, Sequence[str], None] = 'e87c1dee3a2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "body_composition_records" in inspector.get_table_names():
        return

    op.create_table(
        "body_composition_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=True),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("bmi", sa.Float(), nullable=True),
        sa.Column("body_fat_rate", sa.Float(), nullable=True),
        sa.Column("visceral_fat_level", sa.Float(), nullable=True),
        sa.Column("fat_mass", sa.Float(), nullable=True),
        sa.Column("muscle_mass", sa.Float(), nullable=True),
        sa.Column("skeletal_muscle_mass", sa.Float(), nullable=True),
        sa.Column("skeletal_muscle_rate", sa.Float(), nullable=True),
        sa.Column("water_rate", sa.Float(), nullable=True),
        sa.Column("water_mass", sa.Float(), nullable=True),
        sa.Column("bmr", sa.Float(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        sa.ForeignKeyConstraint(["member_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_body_composition_records_id"), "body_composition_records", ["id"], unique=False)
    op.create_index(op.f("ix_body_composition_records_member_id"), "body_composition_records", ["member_id"], unique=False)
    op.create_index(op.f("ix_body_composition_records_assessment_id"), "body_composition_records", ["assessment_id"], unique=False)
    op.create_index(op.f("ix_body_composition_records_measured_at"), "body_composition_records", ["measured_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "body_composition_records" not in inspector.get_table_names():
        return

    op.drop_index(op.f("ix_body_composition_records_measured_at"), table_name="body_composition_records")
    op.drop_index(op.f("ix_body_composition_records_assessment_id"), table_name="body_composition_records")
    op.drop_index(op.f("ix_body_composition_records_member_id"), table_name="body_composition_records")
    op.drop_index(op.f("ix_body_composition_records_id"), table_name="body_composition_records")
    op.drop_table("body_composition_records")
