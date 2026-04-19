"""widen patient_profiles activity_level and budget_level

Revision ID: 20260416_0003
Revises: 20260414_0002
Create Date: 2026-04-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260416_0003"
down_revision: Union[str, None] = "20260414_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "patient_profiles",
        "activity_level",
        type_=sa.Text(),
        existing_type=sa.String(length=20),
        existing_nullable=True,
    )
    op.alter_column(
        "patient_profiles",
        "budget_level",
        type_=sa.Text(),
        existing_type=sa.String(length=20),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "patient_profiles",
        "activity_level",
        type_=sa.String(length=20),
        existing_type=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "patient_profiles",
        "budget_level",
        type_=sa.String(length=20),
        existing_type=sa.Text(),
        existing_nullable=True,
    )
