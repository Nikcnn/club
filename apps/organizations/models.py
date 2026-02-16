from typing import TYPE_CHECKING
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.db.base import Base, TimestampMixin
from apps.users.models import User, UserRole

if TYPE_CHECKING:
    from apps.clubs.models import Club
    from apps.reviews.models import OrganizationReview
    from apps.ratings.models import OrganizationRating

class Organization(User):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    logo_key: Mapped[str | None] = mapped_column(String(512))

    clubs: Mapped[list["Club"]] = relationship(back_populates="organization")
    reviews: Mapped[list["OrganizationReview"]] = relationship(back_populates="organization")
    rating: Mapped["OrganizationRating"] = relationship(back_populates="organization", uselist=False)
    __mapper_args__ = {
        "polymorphic_identity": UserRole.INVESTOR,
    }