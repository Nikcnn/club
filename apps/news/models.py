from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base
from apps.db.mixins import TimestampMixin


class News(Base, TimestampMixin):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(
        ForeignKey("club.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # object storage key для картинки/обложки
    cover_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(nullable=False, server_default="false")

    club: Mapped["Club"] = relationship(back_populates="news")

    __table_args__ = (
        Index("ix_news_club_published", "club_id", "is_published", "published_at"),
    )


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from apps.clubs.models import Club
