from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.db.base import Base
from apps.db.base import TimestampMixin


class AdminUser(Base, TimestampMixin):
    """
    Отдельная таблица под админку, если не хочешь мешать с основной user.
    Если админка будет работать через apps.user.User — этот класс НЕ нужен.
    """
    __tablename__ = "admin_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    __table_args__ = (
        Index("ix_admin_user_login", "login"),
    )
