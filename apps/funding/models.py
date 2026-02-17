import enum
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from apps.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.clubs.models import Club
    from apps.payments.models import Payment
    from apps.users.models import User


# --- ENUMS ---
class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELED = "canceled"


class InvestmentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"




class FundingType(str, enum.Enum):  # <--- ДОБАВИЛ, ИНАЧЕ УПАДЕТ
    DONATION = "donation"
    INVESTMENT = "investment"
    SPONSORSHIP = "sponsorship"


# --- MODELS ---
class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Исправил club.user_id на clubs.id (проверь имя таблицы в apps/clubs/models.py)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    goal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"),
        default=CampaignStatus.DRAFT,
        index=True
    )
    cover_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Исправил определение ARRAY
    gallery_keys: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        default=list,
        server_default="{}"  # Пустой массив в PostgreSQL
    )

    # Убедись, что в модели Club есть relationship(back_populates="campaigns")
    club: Mapped["Club"] = relationship("Club", back_populates="campaigns")

    # Добавляем связь с инвестициями для кампании
    investments: Mapped[List["Investment"]] = relationship("Investment", back_populates="campaign")

    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="check_campaign_dates"),
        CheckConstraint("goal_amount > 0", name="check_campaign_goal_positive"),
    )


class Investment(Base, TimestampMixin):
    __tablename__ = "investments"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="RESTRICT"), index=True)

    # Исправил investor.users_id на investors.id
    investor_id: Mapped[int] = mapped_column(ForeignKey("investors.id", ondelete="CASCADE"), index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    type: Mapped[FundingType] = mapped_column(
        Enum(FundingType, name="funding_type"),
        default=FundingType.DONATION,
        nullable=False
    )
    status: Mapped[InvestmentStatus] = mapped_column(
        Enum(InvestmentStatus, name="investment_status"),
        default=InvestmentStatus.PENDING,
        index=True
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="investments")
    # Тут аккуратно: в модели Investor должно быть back_populates="investments"
    investor: Mapped["User"] = relationship("Investor", back_populates="investments")
    payment: Mapped[Optional["Payment"]] = relationship("Payment", back_populates="investment", uselist=False)

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_investment_amount_positive"),
    )
