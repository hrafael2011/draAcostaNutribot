"""add link_type, make patient_id nullable

Revision ID: 1d20b1323eed
Revises: 658b21298782
Create Date: 2026-06-15 14:43:32.258366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '1d20b1323eed'
down_revision: Union[str, None] = '658b21298782'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add as nullable first, set default, then make NOT NULL
    op.add_column('patient_intake_links', sa.Column('link_type', sa.String(length=20), nullable=True))
    op.execute("UPDATE patient_intake_links SET link_type = 'register' WHERE link_type IS NULL")
    op.alter_column('patient_intake_links', 'link_type', nullable=False)
    op.alter_column('patient_intake_links', 'patient_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('patient_intake_links', 'patient_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('patient_intake_links', 'link_type')
