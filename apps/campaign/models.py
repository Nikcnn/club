import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


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

class PaymentProvide(str, enum.Enum):
    WEBKASA =

class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(
        ForeignKey("club.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text(500), nullable=False)

    goal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status"),
        nullable=False,
        default=CampaignStatus.DRAFT,
        server_default=CampaignStatus.DRAFT.value,
        index=True,
    )

    cover_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    club: Mapped["Club"] = relationship(back_populates="campaigns")
    investments: Mapped[list["Investment"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_campaign_club_status", "club_id", "status"),
    )


class Investment(Base):
    __tablename__ = "investment"

    id: Mapped[int] = mapped_column(primary_key=True)

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaign.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    investor_id: Mapped[int] = mapped_column(
        ForeignKey("investors.user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    status: Mapped[InvestmentStatus] = mapped_column(
        Enum(InvestmentStatus, name="investment_status"),
        nullable=False,
        default=InvestmentStatus.PENDING,
        server_default=InvestmentStatus.PENDING.value,
        index=True,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="investments")
    investor: Mapped["Investor"] = relationship(back_populates="investor")

    payment: Mapped["Payment | None"] = relationship(
        back_populates="investment",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_investment_campaign_user", "campaign_id", "investor_id"),
    )


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(primary_key=True)

    investment_id: Mapped[int] = mapped_column(
        ForeignKey("investment.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_payment_id: Mapped[str] = mapped_column(String(100), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.INIT,
        server_default=PaymentStatus.INIT.value,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    investment: Mapped["Investment"] = relationship(back_populates="payment")

    __table_args__ = (
        UniqueConstraint("provider", "provider_payment_id", name="uq_payment_provider_pid"),
        Index("ix_payment_provider_pid", "provider", "provider_payment_id"),
    )


# Импорт-строки для type checkers (необязательно, но удобно)
from app.clubs.models import Club  # noqa: E402
from app.user.models import User   # noqa: E402
