"""add username column to users

Revision ID: 9a1d2c7ef4b8
Revises: 7f4c3cdb5f01
Create Date: 2026-02-23 00:02:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a1d2c7ef4b8"
down_revision: Union[str, Sequence[str], None] = "7f4c3cdb5f01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=255), nullable=True))
    op.execute("UPDATE users SET username = email WHERE username IS NULL")
    op.alter_column("users", "username", existing_type=sa.String(length=255), nullable=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_column("users", "username")
