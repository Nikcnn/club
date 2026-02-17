"""Add photo_key to competitions

Revision ID: 2f4e7a9b1c22
Revises: 6376c9945e4f
Create Date: 2026-02-17 10:15:00.000000+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2f4e7a9b1c22"
down_revision: Union[str, Sequence[str], None] = "6376c9945e4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("competitions", sa.Column("photo_key", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("competitions", "photo_key")
