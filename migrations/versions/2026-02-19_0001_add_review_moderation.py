"""add review moderation fields

Revision ID: 7f4c3cdb5f01
Revises: e28aba24f681
Create Date: 2026-02-19 00:01:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f4c3cdb5f01"
down_revision: Union[str, Sequence[str], None] = "e28aba24f681"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table_name in ("club_reviews", "organization_reviews"):
        op.add_column(table_name, sa.Column("moderation_status", sa.String(length=16), nullable=True))
        op.add_column(table_name, sa.Column("toxicity_score", sa.Float(), nullable=True))
        op.add_column(table_name, sa.Column("moderation_labels", sa.JSON(), nullable=True))

    op.execute("UPDATE club_reviews SET moderation_status = 'APPROVED', is_approved = true")
    op.execute("UPDATE organization_reviews SET moderation_status = 'APPROVED', is_approved = true")

    op.alter_column("club_reviews", "is_approved", existing_type=sa.Boolean(), nullable=False, server_default=sa.true())
    op.alter_column("organization_reviews", "is_approved", existing_type=sa.Boolean(), nullable=False, server_default=sa.true())

    op.alter_column("club_reviews", "moderation_status", existing_type=sa.String(length=16), nullable=False)
    op.alter_column("organization_reviews", "moderation_status", existing_type=sa.String(length=16), nullable=False)

    op.create_index("ix_club_reviews_is_approved", "club_reviews", ["is_approved"], unique=False)
    op.create_index("ix_organization_reviews_is_approved", "organization_reviews", ["is_approved"], unique=False)
    op.create_index("ix_club_reviews_moderation_status", "club_reviews", ["moderation_status"], unique=False)
    op.create_index("ix_organization_reviews_moderation_status", "organization_reviews", ["moderation_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_organization_reviews_moderation_status", table_name="organization_reviews")
    op.drop_index("ix_club_reviews_moderation_status", table_name="club_reviews")
    op.drop_index("ix_organization_reviews_is_approved", table_name="organization_reviews")
    op.drop_index("ix_club_reviews_is_approved", table_name="club_reviews")

    op.drop_column("organization_reviews", "moderation_labels")
    op.drop_column("organization_reviews", "toxicity_score")
    op.drop_column("organization_reviews", "moderation_status")

    op.drop_column("club_reviews", "moderation_labels")
    op.drop_column("club_reviews", "toxicity_score")
    op.drop_column("club_reviews", "moderation_status")
