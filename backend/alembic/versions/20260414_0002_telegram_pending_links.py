"""telegram pending link codes

Revision ID: 20260414_0002
Revises: 20260413_0001
Create Date: 2026-04-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260414_0002"
down_revision: Union[str, None] = "20260413_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0001 usa metadata.create_all() con los modelos actuales; la tabla puede existir ya.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "telegram_pending_links" in inspector.get_table_names():
        return
    op.create_table(
        "telegram_pending_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_telegram_pending_links_code"),
        "telegram_pending_links",
        ["code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_telegram_pending_links_code"), table_name="telegram_pending_links")
    op.drop_table("telegram_pending_links")
