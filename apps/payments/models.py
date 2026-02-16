import enum

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
    investment_id: Mapped[int] = mapped_column(ForeignKey("investments.id", ondelete="CASCADE"), unique=True)

    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, name="campaign_status"),
        default=PaymentProvider.PAYBOX,
        index=True
    )
    provider_payment_id: Mapped[str] = mapped_column(String(100))
    checkout_url: Mapped[str | None] = mapped_column(String(500))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.INIT
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    investment: Mapped["Investment"] = relationship(back_populates="payment")

    __table_args__ = (
        UniqueConstraint("provider", "provider_payment_id", name="uq_payment_provider_pid"),
    )