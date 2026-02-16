import enum
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text, Numeric, Enum, UniqueConstraint, Index, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.clubs.models import Club
    from apps.users.models import User


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELED = "canceled"


class InvestmentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class PaymentStatus(str, enum.Enum):
    INIT = "init"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELED = "canceled"


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    goal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="KZT")  # ISO code

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"),
        default=CampaignStatus.DRAFT,
        index=True
    )
    cover_key: Mapped[str | None] = mapped_column(String(512))

    club: Mapped["Club"] = relationship(back_populates="campaigns")
    investments: Mapped[list["Investment"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="check_campaign_dates"),
        CheckConstraint("goal_amount > 0", name="check_campaign_goal_positive"),
    )


class Investment(Base, TimestampMixin):
    __tablename__ = "investments"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="RESTRICT"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3))

    status: Mapped[InvestmentStatus] = mapped_column(
        Enum(InvestmentStatus, name="investment_status"),
        default=InvestmentStatus.PENDING,
        index=True
    )
    comment: Mapped[str | None] = mapped_column(String(500))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    campaign: Mapped["Campaign"] = relationship(back_populates="investments")
    user: Mapped["User"] = relationship(back_populates="investments")
    payment: Mapped["Payment"] = relationship(back_populates="investment", uselist=False)

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_investment_amount_positive"),
    )


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    investment_id: Mapped[int] = mapped_column(ForeignKey("investments.id", ondelete="CASCADE"), unique=True)

    provider: Mapped[str] = mapped_column(String(50))  # stripe, kassa24
    provider_payment_id: Mapped[str] = mapped_column(String(100))

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"),
                                                  default=PaymentStatus.INIT)

    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    investment: Mapped["Investment"] = relationship(back_populates="payment")

    __table_args__ = (
        UniqueConstraint("provider", "provider_payment_id", name="uq_payment_provider_pid"),
    )