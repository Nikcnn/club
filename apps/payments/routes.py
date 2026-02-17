from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.users.models import User
from apps.payments.schemas import PaymentInitiate, PaymentResponse, PaymentWebhookData
from apps.payments.services import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


# === CLIENT SIDE ===

@router.post("/initiate", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    schema: PaymentInitiate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    idempotency_key: Optional[str] = Header(default=None, alias="X-Idempotency-Key"),
):
    """
    Шаг 1: Пользователь нажимает "Оплатить".
    Возвращает ссылку на оплату (checkout_url).
    """
    try:
        return await PaymentService.initiate_payment(
            db,
            schema,
            current_user.id,
            idempotency_key=idempotency_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_status(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Проверка статуса платежа.
    """
    payment = await PaymentService.get_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платеж не найден")

    # Проверка доступа: только плательщик может видеть детали
    # (В реальной системе нужно проверять через join с investment, тут упрощенно)
    # if payment.investment.investor_id != current_user.id: ...

    return payment


# === SYSTEM / WEBHOOKS ===

@router.post("/webhook/simulate", response_model=PaymentResponse)
async def simulate_payment_success(
    data: PaymentWebhookData,
    db: AsyncSession = Depends(get_db)
):
    """
    [DEV ONLY] Эмуляция ответа от банка.
    В реальности этот URL вызывает сервер PayBox, а не пользователь.
    Передай сюда 'provider_payment_id', который получил в /initiate, и status='success'.
    """
    is_success = (data.status == 'success')
    try:
        return await PaymentService.process_webhook(db, data.provider_payment_id, is_success)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))