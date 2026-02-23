"""add competition subscriptions

Revision ID: 2f36d1c8b902
Revises: 7f4c3cdb5f01
Create Date: 2026-02-23 17:00:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f36d1c8b902"
down_revision: Union[str, Sequence[str], None] = "7f4c3cdb5f01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "competition_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("competition_id", "user_id", name="uq_competition_subscription"),
    )
    op.create_index("ix_competition_subscriptions_competition_id", "competition_subscriptions", ["competition_id"])
    op.create_index("ix_competition_subscriptions_user_id", "competition_subscriptions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_competition_subscriptions_user_id", table_name="competition_subscriptions")
    op.drop_index("ix_competition_subscriptions_competition_id", table_name="competition_subscriptions")
    op.drop_table("competition_subscriptions")
