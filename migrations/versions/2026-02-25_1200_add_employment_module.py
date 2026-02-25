"""add employment module tables

Revision ID: 1d8b2f71e9aa
Revises: 5afe347ca81d
Create Date: 2026-02-25 12:00:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1d8b2f71e9aa"
down_revision: Union[str, Sequence[str], None] = "5afe347ca81d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


vacancy_status = sa.Enum("draft", "active", "paused", "closed", "archived", name="vacancy_status")
employment_entity_type = sa.Enum("candidate", "organization", name="employment_entity_type")
reaction_action = sa.Enum("like", "dislike", name="reaction_action")
reaction_source = sa.Enum("telegram_bot", "web", name="reaction_source")
match_status = sa.Enum("pending_response", "mutual_matched", "notified", "closed", "expired", "archived", name="employment_match_status")
profile_change_source = sa.Enum("telegram_bot", "web", "system", name="profile_change_source")


def upgrade() -> None:
    vacancy_status.create(op.get_bind(), checkfirst=True)
    employment_entity_type.create(op.get_bind(), checkfirst=True)
    reaction_action.create(op.get_bind(), checkfirst=True)
    reaction_source.create(op.get_bind(), checkfirst=True)
    match_status.create(op.get_bind(), checkfirst=True)
    profile_change_source.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("description_json", sa.JSON(), nullable=False),
        sa.Column("links", sa.JSON(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_candidate_profiles_email", "candidate_profiles", ["email"])
    op.create_index("ix_candidate_profiles_category", "candidate_profiles", ["category"])
    op.create_index("ix_candidate_profiles_city", "candidate_profiles", ["city"])

    op.create_table(
        "tg_info",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.String(length=64), nullable=False),
        sa.Column("telegram_username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("linked_user_id", sa.Integer(), nullable=True),
        sa.Column("linked_candidate_id", sa.Integer(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["linked_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["linked_candidate_id"], ["candidate_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_tg_info_telegram_id", "tg_info", ["telegram_id"])

    op.create_table(
        "vacancies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("position_title", sa.String(length=255), nullable=False),
        sa.Column("description_json", sa.JSON(), nullable=False),
        sa.Column("status", vacancy_status, nullable=False, server_default="draft"),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("employment_type", sa.String(length=64), nullable=True),
        sa.Column("is_remote", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vacancies_organization_id", "vacancies", ["organization_id"])
    op.create_index("ix_vacancies_position_title", "vacancies", ["position_title"])

    op.create_table(
        "club_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_in_club", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("club_id", "user_id", name="uq_club_member"),
    )

    op.create_table(
        "employment_reactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("initiator_entity_type", employment_entity_type, nullable=False),
        sa.Column("initiator_entity_id", sa.Integer(), nullable=False),
        sa.Column("target_entity_type", employment_entity_type, nullable=False),
        sa.Column("target_entity_id", sa.Integer(), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), nullable=True),
        sa.Column("action", reaction_action, nullable=False),
        sa.Column("source", reaction_source, nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_employment_reaction_idempotency"),
        sa.UniqueConstraint(
            "initiator_entity_type",
            "initiator_entity_id",
            "target_entity_type",
            "target_entity_id",
            "vacancy_id",
            name="uq_employment_reaction_target",
        ),
    )
    op.create_index("ix_employment_reactions_vacancy_id", "employment_reactions", ["vacancy_id"])
    op.create_index("ix_employment_reactions_target", "employment_reactions", ["target_entity_type", "target_entity_id"])

    op.create_table(
        "employment_matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("vacancy_id", sa.Integer(), nullable=False),
        sa.Column("status", match_status, nullable=False, server_default="pending_response"),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "organization_id", "vacancy_id", name="uq_employment_match_triplet"),
    )

    op.create_table(
        "candidate_profile_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", sa.JSON(), nullable=False),
        sa.Column("change_source", profile_change_source, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "version_no", name="uq_candidate_profile_history_version"),
    )


def downgrade() -> None:
    op.drop_table("candidate_profile_history")
    op.drop_table("employment_matches")
    op.drop_index("ix_employment_reactions_target", table_name="employment_reactions")
    op.drop_index("ix_employment_reactions_vacancy_id", table_name="employment_reactions")
    op.drop_table("employment_reactions")
    op.drop_table("club_members")
    op.drop_index("ix_vacancies_position_title", table_name="vacancies")
    op.drop_index("ix_vacancies_organization_id", table_name="vacancies")
    op.drop_table("vacancies")
    op.drop_index("ix_tg_info_telegram_id", table_name="tg_info")
    op.drop_table("tg_info")
    op.drop_index("ix_candidate_profiles_city", table_name="candidate_profiles")
    op.drop_index("ix_candidate_profiles_category", table_name="candidate_profiles")
    op.drop_index("ix_candidate_profiles_email", table_name="candidate_profiles")
    op.drop_table("candidate_profiles")

    profile_change_source.drop(op.get_bind(), checkfirst=True)
    match_status.drop(op.get_bind(), checkfirst=True)
    reaction_source.drop(op.get_bind(), checkfirst=True)
    reaction_action.drop(op.get_bind(), checkfirst=True)
    employment_entity_type.drop(op.get_bind(), checkfirst=True)
    vacancy_status.drop(op.get_bind(), checkfirst=True)
