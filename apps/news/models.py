from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base
from apps.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from apps.clubs.models import Club


class News(Base, TimestampMixin):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Исправлено: clubs.id (множественное число, как в таблице клубов)
    club_id: Mapped[int] = mapped_column(
        ForeignKey("clubs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Ссылка на картинку в S3
    cover_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(default=True, server_default="true")

    # Связь с клубом
    club: Mapped["Club"] = relationship("Club", back_populates="news", lazy="selectin")

    __table_args__ = (
        Index("ix_news_club_published", "club_id", "is_published"),
    )