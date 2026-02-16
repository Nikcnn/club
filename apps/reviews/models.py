from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text, Integer, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.users.models import User
    from apps.clubs.models import Club
    from apps.organizations.models import Organization


class ReviewBase(Base, TimestampMixin):
    __abstract__ = True

    text: Mapped[str | None] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer)  # 1-5
    is_approved: Mapped[bool] = mapped_column(default=True)  # Для модерации


class ClubReview(ReviewBase):
    __tablename__ = "club_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    club: Mapped["Club"] = relationship(back_populates="reviews")
    author: Mapped["User"] = relationship(back_populates="club_reviews")

    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_club_review_user"),
        CheckConstraint("score >= 1 AND score <= 5", name="check_club_review_score"),
    )


class OrganizationReview(ReviewBase):
    __tablename__ = "organization_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    organization: Mapped["Organization"] = relationship(back_populates="reviews")
    author: Mapped["User"] = relationship(back_populates="org_reviews")

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_review_user"),
        CheckConstraint("score >= 1 AND score <= 5", name="check_org_review_score"),
    )