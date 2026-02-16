from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base
from apps.db.mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    club_reviews: Mapped[list["ClubReview"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    organization_reviews: Mapped[list["OrganizationReview"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    investor_reviews: Mapped[list["InvestorReview"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_user_email", "email"),
    )



from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from apps.review.models import ClubReview, OrganizationReview, InvestorReview
