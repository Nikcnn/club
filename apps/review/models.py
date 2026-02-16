from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base
from apps.db.mixins import TimestampMixin


class ClubReview(Base, TimestampMixin):
    __tablename__ = "club_review"

    id: Mapped[int] = mapped_column(primary_key=True)

    club_id: Mapped[int] = mapped_column(
        ForeignKey("club.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1..5
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    club: Mapped["Club"] = relationship(back_populates="reviews")
    author: Mapped["User"] = relationship(back_populates="club_reviews")

    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 5", name="ck_club_review_score_1_5"),
        UniqueConstraint("club_id", "author_user_id", name="uq_club_review_club_author"),
        Index("ix_club_review_club_score", "club_id", "score"),
    )


class OrganizationReview(Base, TimestampMixin):
    __tablename__ = "organization_review"

    id: Mapped[int] = mapped_column(primary_key=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1..5
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="reviews")
    author: Mapped["User"] = relationship(back_populates="organization_reviews")

    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 5", name="ck_org_review_score_1_5"),
        UniqueConstraint("organization_id", "author_user_id", name="uq_org_review_org_author"),
        Index("ix_org_review_org_score", "organization_id", "score"),
    )


class InvestorReview(Base, TimestampMixin):
    """
    Отзыв на инвестора (как на участника системы).
    Например: клуб/организация оценивает инвестора или пользователь оценивает инвестора.
    Автор здесь тоже user.
    """
    __tablename__ = "investor_review"

    id: Mapped[int] = mapped_column(primary_key=True)

    investor_id: Mapped[int] = mapped_column(
        ForeignKey("investor.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1..5
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    investor: Mapped["Investor"] = relationship(back_populates="reviews")
    author: Mapped["User"] = relationship(back_populates="investor_reviews")

    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 5", name="ck_investor_review_score_1_5"),
        UniqueConstraint("investor_id", "author_user_id", name="uq_investor_review_investor_author"),
        Index("ix_investor_review_investor_score", "investor_id", "score"),
    )


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from apps.clubs.models import Club
    from apps.organization.models import Organization
    from apps.user.models import User
    from apps.user.models import Investor  # см. ниже
