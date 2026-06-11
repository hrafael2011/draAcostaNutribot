"""0007_remove_telegram_tables

Revision ID: f8242b498188
Revises: 20260425_0006
Create Date: 2026-06-10 21:55:08.255569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = 'f8242b498188'
down_revision: Union[str, None] = '20260425_0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("conversation_states")
    op.drop_table("doctor_telegram_bindings")
    op.drop_table("telegram_pending_links")
    op.drop_table("telegram_processed_updates")
    op.drop_column("doctors", "telegram_user_id")
    op.drop_column("doctors", "telegram_username")

def downgrade() -> None:
    # Recrear columnas en doctors
    op.add_column("doctors", sa.Column("telegram_user_id", sa.String(40), nullable=True))
    op.add_column("doctors", sa.Column("telegram_username", sa.String(120), nullable=True))
    # Las tablas no se recrean (datos ya perdidos)
