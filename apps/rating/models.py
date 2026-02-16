from sqlalchemy import ForeignKey, Index, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base
from apps.db.mixins import TimestampMixin


class ClubRating(Base, TimestampMixin):
    __tablename__ = "club_rating"

    id: Mapped[int] = mapped_column(primary_key=True)

    club_id: Mapped[int] = mapped_column(
        ForeignKey("club.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # 1:1
        index=True,
    )

    reviews_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    avg_score: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, server_default="0")

    club: Mapped["Club"] = relationship(back_populates="rating")

    __table_args__ = (
        UniqueConstraint("club_id", name="uq_club_rating_club_id"),
        Index("ix_club_rating_avg", "avg_score"),
    )


class OrganizationRating(Base, TimestampMixin):
    __tablename__ = "organization_rating"

    id: Mapped[int] = mapped_column(primary_key=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    reviews_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    avg_score: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, server_default="0")

    organization: Mapped["Organization"] = relationship(back_populates="rating")

    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_org_rating_org_id"),
        Index("ix_org_rating_avg", "avg_score"),
    )


class InvestorRating(Base, TimestampMixin):
    __tablename__ = "investor_rating"

    id: Mapped[int] = mapped_column(primary_key=True)

    investor_id: Mapped[int] = mapped_column(
        ForeignKey("investor.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    reviews_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    avg_score: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, server_default="0")

    investor: Mapped["Investor"] = relationship(back_populates="rating")

    __table_args__ = (
        UniqueConstraint("investor_id", name="uq_investor_rating_investor_id"),
        Index("ix_investor_rating_avg", "avg_score"),
    )


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from apps.clubs.models import Club
    from apps.organizations.models import Organization
    from apps.users.models import Investor
