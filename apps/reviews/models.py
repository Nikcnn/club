from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text, Integer, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.db.base import Base
from apps.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from apps.users.models import User
    from apps.clubs.models import Club
    # from apps.organizations.models import Organization # Раскомментировать, когда появится модуль

class ReviewBase(Base, TimestampMixin):
    __abstract__ = True

    text: Mapped[str | None] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    is_approved: Mapped[bool] = mapped_column(default=True)  # Для модерации (можно расширить)

class ClubReview(ReviewBase):
    __tablename__ = "club_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    club: Mapped["Club"] = relationship("Club", backref="reviews", lazy="selectin")
    author: Mapped["User"] = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_club_review_user"),
        CheckConstraint("score >= 1 AND score <= 5", name="check_club_review_score"),
    )

class OrganizationReview(ReviewBase):
    __tablename__ = "organization_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # organization: Mapped["Organization"] = relationship("Organization", backref="reviews")
    author: Mapped["User"] = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_review_user"),
        CheckConstraint("score >= 1 AND score <= 5", name="check_org_review_score"),
    )