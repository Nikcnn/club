import enum
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    # Импорты для Type Checking, чтобы IDE понимала связи
    pass
class UserRole(str, enum.Enum):
    MEMBER = "member"           # Обычный пользователь (гость)
    CLUB = "club"               # Клуб
    ORGANIZATION = "organization" # Организатор
    INVESTOR = "investor"       # Инвестор


class SQLAlchemyEnum:
    pass


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole, name="user_role", native_enum=True),  # native_enum=True создает тип в Postgres
        nullable=False,
        index=True
    )

    avatar_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    __mapper_args__ = {
        "polymorphic_identity": UserRole.MEMBER,  # По дефолту, если создаем просто User
        "polymorphic_on": role,  # SQLAlchemy смотрит на эту колонку
    }