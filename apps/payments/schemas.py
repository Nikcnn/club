from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from apps.payments.models import PaymentProvider, PaymentStatus

# === INITIATE ===
class PaymentInitiate(BaseModel):
    investment_id: int = Field(..., description="ID инвестиции, которую нужно оплатить")
    provider: PaymentProvider = Field(default=PaymentProvider.PAYBOX)

# === WEBHOOK (Simulated) ===
class PaymentWebhookData(BaseModel):
    """
    Схема данных, которые присылает платежка (упрощенно)
    """
    provider_payment_id: str
    status: str  # 'success' / 'error'
    signature: Optional[str] = None # Для проверки подлинности

# === RESPONSE ===
class PaymentResponse(BaseModel):
    id: int
    investment_id: int
    amount: Decimal
    status: PaymentStatus
    provider: PaymentProvider
    checkout_url: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)