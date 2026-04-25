"""doctor roles and forced password change

Revision ID: 20260425_0006
Revises: 20260419_0005
Create Date: 2026-04-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260425_0006"
down_revision: Union[str, None] = "20260419_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("doctors")}

    if "role" not in columns:
        op.add_column(
            "doctors",
            sa.Column(
                "role",
                sa.String(length=20),
                nullable=False,
                server_default="doctor",
            ),
        )
    if "must_change_password" not in columns:
        op.add_column(
            "doctors",
            sa.Column(
                "must_change_password",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

    op.execute("UPDATE doctors SET role = 'doctor' WHERE role IS NULL OR role = ''")
    op.execute(
        "UPDATE doctors SET must_change_password = false "
        "WHERE must_change_password IS NULL"
    )

    if "role" not in columns:
        op.alter_column("doctors", "role", server_default=None)
    if "must_change_password" not in columns:
        op.alter_column("doctors", "must_change_password", server_default=None)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col["name"] for col in inspector.get_columns("doctors")}

    if "must_change_password" in columns:
        op.drop_column("doctors", "must_change_password")
    if "role" in columns:
        op.drop_column("doctors", "role")
