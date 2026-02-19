from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.payments.schemas import PaymentInitiate, PaymentResponse, PaymentWebhookData
from apps.payments.services import DomainTransitionError, PaymentService
from apps.users.dependencies import get_current_user
from apps.users.models import User

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/initiate", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    schema: PaymentInitiate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await PaymentService.initiate_payment(db, schema, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_status(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = await PaymentService.get_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платеж не найден")
    return payment


@router.post("/webhook/simulate", response_model=PaymentResponse)
async def simulate_payment_success(
    data: PaymentWebhookData,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await PaymentService.handle_webhook(db, data, headers=request.headers)
    except DomainTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
