from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.users.models import User, UserRole

if TYPE_CHECKING:
    # Импорты для Type Hinting
    from apps.reviews.models import OrganizationReview
    from apps.ratings.models import OrganizationRating
    # from apps.competitions.models import Competition # Если организации создают турниры


class Organization(User):
    __tablename__ = "organizations"

    # Внешний ключ на родительскую таблицу users
    id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    name: Mapped[str] = mapped_column(String(200), index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Медиа
    logo_key: Mapped[Optional[str]] = mapped_column(String(512))
    website: Mapped[Optional[str]] = mapped_column(String(255))

    # Связи
    reviews: Mapped[List["OrganizationReview"]] = relationship(
        "OrganizationReview",
        # back_populates="organization", # Если настроено в Review
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Рейтинг (One-to-One)
    rating: Mapped["OrganizationRating"] = relationship(
        "OrganizationRating",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    __mapper_args__ = {
        "polymorphic_identity": UserRole.ORGANIZATION,  # ИСПРАВЛЕНО
    }