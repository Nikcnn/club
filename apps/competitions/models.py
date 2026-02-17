import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base
# Предполагается, что TimestampMixin добавляет created_at/updated_at
from apps.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from apps.clubs.models import Club

class CompetitionStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELED = "canceled"

class Competition(Base, TimestampMixin):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Исправлено: ссылка на таблицу 'clubs', а не 'club'
    club_id: Mapped[int] = mapped_column(
        ForeignKey("clubs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    photo_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    status: Mapped[CompetitionStatus] = mapped_column(
        Enum(CompetitionStatus, name="competition_status"),
        default=CompetitionStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Связь с клубом-организатором
    club: Mapped["Club"] = relationship("Club", back_populates="competitions", lazy="selectin")

    __table_args__ = (
        Index("ix_competition_dates", "starts_at", "ends_at"),
    )