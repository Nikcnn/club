"""add search tracking and personalization tables

Revision ID: c3b92c71aa10
Revises: a9d2f7c1e301, 3366d041159c
Create Date: 2026-02-18 12:00:00.000000+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3b92c71aa10"
down_revision: Union[str, Sequence[str], None] = ("a9d2f7c1e301", "3366d041159c")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("query_text", sa.String(length=512), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("filters_json", sa.JSON(), nullable=True),
        sa.Column("top_doc_ids", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_events_user_id", "search_events", ["user_id"], unique=False)
    op.create_index("ix_search_events_created_at", "search_events", ["created_at"], unique=False)

    op.create_table(
        "click_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("doc_id", sa.String(length=255), nullable=False),
        sa.Column("doc_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("query_text", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_click_events_user_id", "click_events", ["user_id"], unique=False)
    op.create_index("ix_click_events_doc_id", "click_events", ["doc_id"], unique=False)
    op.create_index("ix_click_events_doc_type", "click_events", ["doc_type"], unique=False)
    op.create_index("ix_click_events_created_at", "click_events", ["created_at"], unique=False)

    op.create_table(
        "user_search_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("top_cities", sa.JSON(), nullable=False),
        sa.Column("top_categories", sa.JSON(), nullable=False),
        sa.Column("top_types", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_search_profiles")

    op.drop_index("ix_click_events_created_at", table_name="click_events")
    op.drop_index("ix_click_events_doc_type", table_name="click_events")
    op.drop_index("ix_click_events_doc_id", table_name="click_events")
    op.drop_index("ix_click_events_user_id", table_name="click_events")
    op.drop_table("click_events")

    op.drop_index("ix_search_events_created_at", table_name="search_events")
    op.drop_index("ix_search_events_user_id", table_name="search_events")
    op.drop_table("search_events")
