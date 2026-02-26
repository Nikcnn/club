from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from apps.payments.models import PaymentProvider, PaymentStatus


class PaymentInitiate(BaseModel):
    investment_id: int = Field(..., description="ID инвестиции, которую нужно оплатить")
    provider: PaymentProvider = Field(default=PaymentProvider.PAYBOX)
    idempotency_key: Optional[str] = Field(default=None, max_length=128)


class PaymentWebhookData(BaseModel):
    provider_payment_id: str
    provider_event_id: Optional[str] = None
    event_type: str = "payment_status"
    status: str
    signature: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PaymentResponse(BaseModel):
    id: int
    investment_id: int
    amount: Decimal
    status: PaymentStatus
    provider: PaymentProvider
    provider_payment_id: str
    checkout_url: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
