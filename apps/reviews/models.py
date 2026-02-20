import enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.clubs.models import Club
    from apps.organizations.models import Organization
    from apps.users.models import User


class ModerationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewBase(Base, TimestampMixin):
    __abstract__ = True

    text: Mapped[str | None] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer)  # 1-5
    is_approved: Mapped[bool] = mapped_column(default=True, index=True)
    moderation_status: Mapped[str] = mapped_column(String(16), default=ModerationStatus.PENDING.value, index=True)
    toxicity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    moderation_labels: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ClubReview(ReviewBase):
    __tablename__ = "club_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    club: Mapped["Club"] = relationship(
        "Club",
        back_populates="reviews",
        foreign_keys=[club_id],
    )

    author: Mapped["User"] = relationship(
        "User",
        back_populates="club_reviews",
        foreign_keys=[user_id],
    )

    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_club_review_user"),
        CheckConstraint("score >= 1 AND score <= 5", name="check_club_review_score"),
    )


class OrganizationReview(ReviewBase):
    __tablename__ = "organization_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="reviews",
        foreign_keys=[organization_id],
    )

    author: Mapped["User"] = relationship(
        "User",
        back_populates="org_reviews",
        foreign_keys=[user_id],
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_review_user"),
        CheckConstraint("score >= 1 AND score <= 5", name="check_org_review_score"),
    )
