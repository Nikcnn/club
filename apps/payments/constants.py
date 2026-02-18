from apps.payments.models import PaymentStatus

ALLOWED_PAYMENT_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.CREATED: {PaymentStatus.PENDING, PaymentStatus.CANCELED},
    PaymentStatus.PENDING: {PaymentStatus.SUCCESS, PaymentStatus.FAILED, PaymentStatus.CANCELED},
    PaymentStatus.SUCCESS: {PaymentStatus.REFUNDED},
    PaymentStatus.FAILED: {PaymentStatus.PENDING},
    PaymentStatus.CANCELED: set(),
    PaymentStatus.REFUNDED: set(),
}
