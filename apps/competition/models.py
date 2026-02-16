import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base
from apps.db.mixins import TimestampMixin


class CompetitionStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELED = "canceled"


class Competition(Base, TimestampMixin):
    __tablename__ = "competition"

    id: Mapped[int] = mapped_column(primary_key=True)

    club_id: Mapped[int] = mapped_column(
        ForeignKey("club.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[CompetitionStatus] = mapped_column(
        Enum(CompetitionStatus, name="competition_status"),
        nullable=False,
        index=True,
        server_default=CompetitionStatus.DRAFT.value,
    )

    club: Mapped["Club"] = relationship(back_populates="competitions")

    __table_args__ = (
        Index("ix_competition_club_status", "club_id", "status"),
        Index("ix_competition_dates", "starts_at", "ends_at"),
    )


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from apps.clubs.models import Club
