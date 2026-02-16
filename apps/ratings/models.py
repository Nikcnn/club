from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.clubs.models import Club
    from apps.organizations.models import Organization


class RatingBase(Base, TimestampMixin):
    __abstract__ = True
    avg_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)  # e.g. 4.55
    review_count: Mapped[int] = mapped_column(Integer, default=0)


class ClubRating(RatingBase):
    __tablename__ = "club_ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), unique=True)

    club: Mapped["Club"] = relationship(back_populates="rating")


class OrganizationRating(RatingBase):
    __tablename__ = "organization_ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), unique=True)

    organization: Mapped["Organization"] = relationship(back_populates="rating")