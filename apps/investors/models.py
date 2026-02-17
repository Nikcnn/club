from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.users.models import User, UserRole

if TYPE_CHECKING:
    from apps.funding.models import Investment


class Investor(User):
    __tablename__ = "investors"

    # Внешний ключ на родительскую таблицу users
    id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    # Специфичные поля инвестора
    bio: Mapped[Optional[str]] = mapped_column(Text)
    company_name: Mapped[Optional[str]] = mapped_column(String(150))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(255))

    # Связь с инвестициями (lazy="selectin" для асинхронной подгрузки)
    investments: Mapped[List["Investment"]] = relationship(
        "Investment",
        back_populates="investor",
        lazy="selectin"
    )

    # Настройка полиморфизма
    __mapper_args__ = {
        "polymorphic_identity": UserRole.INVESTOR,
    }