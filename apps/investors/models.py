from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.db.base import Base

if TYPE_CHECKING:
    from apps.users.models import User, UserRole


class Investor(User):
    __tablename__ = "investors"

    id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    bio: Mapped[str | None] = mapped_column(String, nullable=True)
    # Доп. поля инвестора

    user: Mapped["User"] = relationship(back_populates="investor_profile")

    __mapper_args__ = {
        "polymorphic_identity": UserRole.INVESTOR,
    }