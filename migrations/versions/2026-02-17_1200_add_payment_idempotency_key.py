"""Add idempotency key to payments

Revision ID: 9d1c4a7e2b10
Revises: 2f4e7a9b1c22
Create Date: 2026-02-17 12:00:00.000000+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d1c4a7e2b10"
down_revision: Union[str, Sequence[str], None] = "2f4e7a9b1c22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_payments_idempotency_key"), "payments", ["idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_payments_idempotency_key"), table_name="payments")
    op.drop_column("payments", "idempotency_key")
