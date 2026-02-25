from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, Index, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base, TimestampMixin
from apps.employment.enums import (
    EntityType,
    MatchStatus,
    ProfileChangeSource,
    ReactionAction,
    ReactionSource,
    VacancyStatus,
)


class TgInfo(Base, TimestampMixin):
    __tablename__ = "tg_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    linked_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    linked_candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="SET NULL"), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CandidateProfile(Base, TimestampMixin):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    links: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    resume_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    history: Mapped[list["CandidateProfileHistory"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class Vacancy(Base, TimestampMixin):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    position_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[VacancyStatus] = mapped_column(Enum(VacancyStatus, name="vacancy_status", native_enum=True), nullable=False, default=VacancyStatus.DRAFT, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ClubMember(Base, TimestampMixin):
    __tablename__ = "club_members"
    __table_args__ = (UniqueConstraint("club_id", "user_id", name="uq_club_member"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_in_club: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EmploymentReaction(Base):
    __tablename__ = "employment_reactions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_employment_reaction_idempotency"),
        UniqueConstraint(
            "initiator_entity_type",
            "initiator_entity_id",
            "target_entity_type",
            "target_entity_id",
            "vacancy_id",
            name="uq_employment_reaction_target",
        ),
        Index("ix_employment_reactions_target", "target_entity_type", "target_entity_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    initiator_entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType, name="employment_entity_type", native_enum=True), nullable=False)
    initiator_entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType, name="employment_entity_type", native_enum=True), nullable=False)
    target_entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    vacancy_id: Mapped[Optional[int]] = mapped_column(ForeignKey("vacancies.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[ReactionAction] = mapped_column(Enum(ReactionAction, name="reaction_action", native_enum=True), nullable=False)
    source: Mapped[ReactionSource] = mapped_column(Enum(ReactionSource, name="reaction_source", native_enum=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class EmploymentMatch(Base, TimestampMixin):
    __tablename__ = "employment_matches"
    __table_args__ = (UniqueConstraint("candidate_id", "organization_id", "vacancy_id", name="uq_employment_match_triplet"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus, name="employment_match_status", native_enum=True), nullable=False, default=MatchStatus.PENDING_RESPONSE, index=True)
    matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CandidateProfileHistory(Base):
    __tablename__ = "candidate_profile_history"
    __table_args__ = (UniqueConstraint("candidate_id", "version_no", name="uq_candidate_profile_history_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    change_source: Mapped[ProfileChangeSource] = mapped_column(Enum(ProfileChangeSource, name="profile_change_source", native_enum=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    candidate: Mapped[CandidateProfile] = relationship(back_populates="history")
