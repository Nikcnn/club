import enum
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional  # Добавил List
from sqlalchemy import ForeignKey, String, Text, Numeric, Enum, UniqueConstraint, Index, CheckConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY  # <--- ВАЖНО

from apps.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.clubs.models import Club
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




class PaymentProvider(str, enum.Enum):
    PAYBOX = "paybox"
    STRIPE = "stripe"


class PaymentStatus(str, enum.Enum):
    INIT = "init"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


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


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    investment_id: Mapped[int] = mapped_column(ForeignKey("investments.id", ondelete="CASCADE"), unique=True)

    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, name="payment_provider"),
        default=PaymentProvider.PAYBOX,
        index=True,
    )
    provider_payment_id: Mapped[str] = mapped_column(String(100))
    checkout_url: Mapped[str | None] = mapped_column(String(500))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.INIT,
    )

    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    investment: Mapped["Investment"] = relationship("Investment", back_populates="payment")

    __table_args__ = (
        UniqueConstraint("provider", "provider_payment_id", name="uq_payment_provider_pid"),
    )
