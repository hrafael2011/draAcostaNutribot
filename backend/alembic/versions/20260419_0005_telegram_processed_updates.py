"""telegram webhook processed update ids

Revision ID: 20260419_0005
Revises: 20260417_0004
Create Date: 2026-04-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260419_0005"
down_revision: Union[str, None] = "20260417_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "telegram_processed_updates" in inspector.get_table_names():
        return
    op.create_table(
        "telegram_processed_updates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("update_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_telegram_processed_updates_id"),
        "telegram_processed_updates",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telegram_processed_updates_update_id"),
        "telegram_processed_updates",
        ["update_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_telegram_processed_updates_update_id"),
        table_name="telegram_processed_updates",
    )
    op.drop_index(
        op.f("ix_telegram_processed_updates_id"),
        table_name="telegram_processed_updates",
    )
    op.drop_table("telegram_processed_updates")
