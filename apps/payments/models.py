import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.funding.models import Investment


class PaymentProvider(str, enum.Enum):
    PAYBOX = "paybox"
    STRIPE = "stripe"


class PaymentStatus(str, enum.Enum):
    INIT = "init"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    investment_id: Mapped[int] = mapped_column(ForeignKey("investments.id", ondelete="CASCADE"), unique=True, index=True)

    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, name="payment_provider"),
        default=PaymentProvider.PAYBOX,
        index=True,
    )
    provider_payment_id: Mapped[str] = mapped_column(String(100))
    checkout_url: Mapped[Optional[str]] = mapped_column(String(500))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.INIT,
        index=True,
    )

    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    investment: Mapped["Investment"] = relationship("Investment", back_populates="payment")

    __table_args__ = (
        UniqueConstraint("provider", "provider_payment_id", name="uq_payment_provider_pid"),
    )
