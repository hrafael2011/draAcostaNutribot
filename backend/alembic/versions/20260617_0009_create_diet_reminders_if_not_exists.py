"""create diet_reminders if not exists

Revision ID: 9a1b2c3d4e5f
Revises: 417863aa21ba
Create Date: 2026-06-17 17:30:00.000000

This migration creates the diet_reminders table on databases where the
previous migration (68f37ec7c532) was applied but was empty.
Uses IF NOT EXISTS to be safe for fresh deployments where the fixed
68f37ec7c532 already created the table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a1b2c3d4e5f'
down_revision: Union[str, None] = '417863aa21ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS diet_reminders (
            id SERIAL PRIMARY KEY,
            diet_id INTEGER NOT NULL REFERENCES diets(id),
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            intake_link_id INTEGER NOT NULL REFERENCES patient_intake_links(id),
            sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            sent_to_email VARCHAR(190) NOT NULL
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_diet_reminders_id ON diet_reminders (id)
    """)


def downgrade() -> None:
    op.drop_index(op.f("ix_diet_reminders_id"), table_name="diet_reminders")
    op.drop_table("diet_reminders")
