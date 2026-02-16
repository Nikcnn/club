from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.users.models import User, UserRole

if TYPE_CHECKING:
    # Импорты для Type Hinting, чтобы избежать цикличных ссылок в runtime
    from apps.funding.models import Campaign


class Club(User):
    __tablename__ = "clubs"

    # Внешний ключ на родительскую таблицу users
    id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    # Специфичные поля клуба
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100), index=True)  # IT, Sport, Art
    city: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Медиа и контакты
    logo_key: Mapped[Optional[str]] = mapped_column(String(512))  # Ссылка на S3
    website: Mapped[Optional[str]] = mapped_column(String(255))
    social_links: Mapped[Optional[dict]] = mapped_column(JSON, default={})  # {"instagram": "...", "telegram": "..."}

    # Связи (Relationships)
    # lazy="selectin" используется для эффективной асинхронной подгрузки
    campaigns: Mapped[List["Campaign"]] = relationship(
        "Campaign",
        back_populates="club",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Настройка полиморфизма SQLAlchemy
    __mapper_args__ = {
        "polymorphic_identity": UserRole.CLUB,
    }