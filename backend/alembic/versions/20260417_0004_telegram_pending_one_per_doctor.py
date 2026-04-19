"""one telegram pending link row per doctor

Revision ID: 20260417_0004
Revises: 20260416_0003
Create Date: 2026-04-17

Keeps the oldest row (smaller id) per doctor_id and adds UNIQUE(doctor_id).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260417_0004"
down_revision: Union[str, None] = "20260416_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "ix_telegram_pending_links_doctor_id"


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "telegram_pending_links" not in inspector.get_table_names():
        return

    for ix in inspector.get_indexes("telegram_pending_links"):
        if ix.get("column_names") == ["doctor_id"] and ix.get("unique"):
            return

    op.execute(
        sa.text(
            """
            DELETE FROM telegram_pending_links AS a
            USING telegram_pending_links AS b
            WHERE a.doctor_id = b.doctor_id AND a.id > b.id
            """
        )
    )

    op.create_index(
        INDEX_NAME,
        "telegram_pending_links",
        ["doctor_id"],
        unique=True,
    )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "telegram_pending_links" not in inspector.get_table_names():
        return

    for ix in inspector.get_indexes("telegram_pending_links"):
        if ix.get("column_names") == ["doctor_id"] and ix.get("unique"):
            op.drop_index(ix["name"], table_name="telegram_pending_links")
            return
