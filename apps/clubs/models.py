from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.db.base import Base, TimestampMixin
from apps.users.models import User, UserRole

if TYPE_CHECKING:
    from apps.organizations.models import Organization
    from apps.campaigns.models import Campaign
    from apps.reviews.models import ClubReview
    from apps.ratings.models import ClubRating


class Club(User):
    __tablename__ = "clubs"

    id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))

    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100), index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text)
    logo_key: Mapped[str | None] = mapped_column(String(512))

    organization: Mapped["Organization"] = relationship(back_populates="clubs")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="club")

    reviews: Mapped[list["ClubReview"]] = relationship(back_populates="club")
    rating: Mapped["ClubRating"] = relationship(back_populates="club", uselist=False)
    __mapper_args__ = {
        "polymorphic_identity": UserRole.CLUB,  # <--- Ссылка на Enum
    }