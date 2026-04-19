"""initial schema from SQLAlchemy models

Revision ID: 20260413_0001
Revises:
Create Date: 2026-04-13

"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260413_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    import app.models  # noqa: F401
    from app.core.database import Base

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    import app.models  # noqa: F401
    from app.core.database import Base

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
