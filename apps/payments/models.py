import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.funding.models import Investment


class PaymentProvider(str, enum.Enum):
    PAYBOX = "paybox"
    STRIPE = "stripe"


class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class PaymentActorType(str, enum.Enum):
    SYSTEM = "system"
    USER = "user"
    WEBHOOK = "webhook"


class WebhookEventStatus(str, enum.Enum):
    RECEIVED = "received"
    PROCESSED = "processed"
    IGNORED = "ignored"
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
    provider_payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    checkout_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.CREATED,
        index=True,
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_event_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    investment: Mapped["Investment"] = relationship("Investment", back_populates="payment")
    transitions: Mapped[list["PaymentStateTransitionLog"]] = relationship(
        "PaymentStateTransitionLog", back_populates="payment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("provider", "provider_payment_id", name="uq_payment_provider_pid"),
        Index("idx_payment_status_created", "status", "created_at"),
    )


class PaymentIdempotency(Base):
    __tablename__ = "payment_idempotency"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    scope: Mapped[str] = mapped_column(String(64), default="initiate_payment")
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"))
    response_code: Mapped[int] = mapped_column(Integer, default=201)
    response_body: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "scope", "idempotency_key", name="uq_payment_idempotency_user_scope_key"),
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    provider_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str] = mapped_column(String(128))
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict] = mapped_column(JSON)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[WebhookEventStatus] = mapped_column(
        Enum(WebhookEventStatus, name="webhook_event_status"), default=WebhookEventStatus.RECEIVED, index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    deliveries: Mapped[list["WebhookDeliveryLog"]] = relationship(
        "WebhookDeliveryLog", back_populates="webhook_event", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_webhook_provider_event"),
        UniqueConstraint("provider", "payload_hash", name="uq_webhook_provider_hash"),
        Index("idx_webhook_status_received", "status", "received_at"),
    )


class WebhookDeliveryLog(Base):
    __tablename__ = "webhook_delivery_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    webhook_event_id: Mapped[int] = mapped_column(ForeignKey("webhook_events.id", ondelete="CASCADE"), index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    http_headers: Mapped[dict] = mapped_column(JSON)
    remote_addr: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    webhook_event: Mapped[WebhookEvent] = relationship("WebhookEvent", back_populates="deliveries")

    __table_args__ = (
        UniqueConstraint("webhook_event_id", "attempt_no", name="uq_delivery_attempt"),
    )


class PaymentStateTransitionLog(Base):
    __tablename__ = "payment_state_transition_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), index=True)
    from_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"))
    to_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"))
    reason: Mapped[str] = mapped_column(String(255))
    actor_type: Mapped[PaymentActorType] = mapped_column(Enum(PaymentActorType, name="payment_actor_type"))
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    payment: Mapped[Payment] = relationship("Payment", back_populates="transitions")

    __table_args__ = (Index("idx_payment_transition_payment_created", "payment_id", "created_at"),)
