import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Optional

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.funding.models import Investment, InvestmentStatus
from apps.payments.constants import ALLOWED_PAYMENT_TRANSITIONS
from apps.payments.models import (
    Payment,
    PaymentActorType,
    PaymentIdempotency,
    PaymentProvider,
    PaymentStateTransitionLog,
    PaymentStatus,
    WebhookDeliveryLog,
    WebhookEvent,
    WebhookEventStatus,
)
from apps.payments.schemas import PaymentInitiate, PaymentWebhookData


@dataclass
class ActorCtx:
    actor_type: PaymentActorType
    actor_id: Optional[int] = None


class DomainTransitionError(ValueError):
    pass


class PaymentService:
    @staticmethod
    def _hash_payload(payload: dict) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    async def _get_investment_for_update(db: AsyncSession, investment_id: int) -> Optional[Investment]:
        query: Select[tuple[Investment]] = select(Investment).where(Investment.id == investment_id).with_for_update()
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def initiate_payment(db: AsyncSession, schema: PaymentInitiate, user_id: int) -> Payment:
        request_payload = {
            "investment_id": schema.investment_id,
            "provider": schema.provider.value,
        }
        request_hash = PaymentService._hash_payload(request_payload)

        async with db.begin():
            if schema.idempotency_key:
                idem_q = select(PaymentIdempotency).where(
                    PaymentIdempotency.user_id == user_id,
                    PaymentIdempotency.scope == "initiate_payment",
                    PaymentIdempotency.idempotency_key == schema.idempotency_key,
                )
                idem = (await db.execute(idem_q)).scalar_one_or_none()
                if idem:
                    payment = await db.get(Payment, idem.payment_id)
                    if payment:
                        return payment

            investment = await PaymentService._get_investment_for_update(db, schema.investment_id)
            if not investment:
                raise ValueError("Инвестиция не найдена")
            if investment.investor_id != user_id:
                raise ValueError("Вы не можете оплатить чужую инвестицию")
            if investment.status == InvestmentStatus.PAID:
                raise ValueError("Эта инвестиция уже оплачена")

            existing_payment = (
                await db.execute(select(Payment).where(Payment.investment_id == investment.id).with_for_update())
            ).scalar_one_or_none()

            provider_id = str(uuid.uuid4())
            checkout_url = f"https://paybox.money/pay/{provider_id}"

            if existing_payment:
                if existing_payment.status == PaymentStatus.SUCCESS:
                    raise ValueError("Платеж уже прошел успешно")
                existing_payment.provider = schema.provider
                existing_payment.provider_payment_id = provider_id
                existing_payment.checkout_url = checkout_url
                existing_payment.status = PaymentStatus.PENDING
                existing_payment.idempotency_key = schema.idempotency_key
                existing_payment.last_event_at = datetime.now(timezone.utc)
                existing_payment.version += 1
                payment = existing_payment
            else:
                payment = Payment(
                    investment_id=investment.id,
                    amount=investment.amount,
                    provider=schema.provider,
                    provider_payment_id=provider_id,
                    checkout_url=checkout_url,
                    status=PaymentStatus.PENDING,
                    idempotency_key=schema.idempotency_key,
                    last_event_at=datetime.now(timezone.utc),
                )
                db.add(payment)
                await db.flush()

            if schema.idempotency_key:
                db.add(
                    PaymentIdempotency(
                        user_id=user_id,
                        scope="initiate_payment",
                        idempotency_key=schema.idempotency_key,
                        request_hash=request_hash,
                        payment_id=payment.id,
                        response_code=201,
                        response_body={
                            "payment_id": payment.id,
                            "investment_id": payment.investment_id,
                            "status": payment.status.value,
                        },
                        created_at=datetime.now(timezone.utc),
                    )
                )

        await db.refresh(payment)
        return payment

    @staticmethod
    async def transition_payment(
        db: AsyncSession,
        payment: Payment,
        to_status: PaymentStatus,
        reason: str,
        actor: ActorCtx,
    ) -> Payment:
        from_status = payment.status
        if from_status == to_status:
            return payment
        allowed = ALLOWED_PAYMENT_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise DomainTransitionError(f"Illegal payment transition: {from_status.value} -> {to_status.value}")

        payment.status = to_status
        payment.last_event_at = datetime.now(timezone.utc)
        payment.version += 1
        if to_status == PaymentStatus.SUCCESS:
            payment.confirmed_at = datetime.now(timezone.utc)

        db.add(
            PaymentStateTransitionLog(
                payment_id=payment.id,
                from_status=from_status,
                to_status=to_status,
                reason=reason,
                actor_type=actor.actor_type,
                actor_id=actor.actor_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        return payment

    @staticmethod
    async def process_webhook(
        db: AsyncSession,
        provider_payment_id: str,
        is_success: bool,
        provider_event_id: Optional[str] = None,
        payload: Optional[dict] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Payment:
        payload = payload or {"provider_payment_id": provider_payment_id, "status": "success" if is_success else "failed"}
        payload_hash = PaymentService._hash_payload(payload)

        async with db.begin():
            duplicate_event = (
                await db.execute(
                    select(WebhookEvent).where(
                        WebhookEvent.provider == PaymentProvider.PAYBOX.value,
                        (
                            (WebhookEvent.provider_event_id == provider_event_id)
                            if provider_event_id
                            else (WebhookEvent.payload_hash == payload_hash)
                        ),
                    )
                )
            ).scalar_one_or_none()
            if duplicate_event:
                payment_q = select(Payment).where(Payment.provider_payment_id == provider_payment_id)
                existing = (await db.execute(payment_q)).scalar_one_or_none()
                if not existing:
                    raise ValueError("Платеж не найден")
                return existing

            webhook_event = WebhookEvent(
                provider=PaymentProvider.PAYBOX.value,
                provider_event_id=provider_event_id,
                event_type="payment_status",
                signature_valid=True,
                payload=payload,
                payload_hash=payload_hash,
                received_at=datetime.now(timezone.utc),
                status=WebhookEventStatus.RECEIVED,
            )
            db.add(webhook_event)
            await db.flush()

            db.add(
                WebhookDeliveryLog(
                    webhook_event_id=webhook_event.id,
                    attempt_no=1,
                    http_headers=dict(headers or {}),
                    remote_addr=None,
                    processed=True,
                    http_status=200,
                    created_at=datetime.now(timezone.utc),
                )
            )

            payment = (
                await db.execute(select(Payment).where(Payment.provider_payment_id == provider_payment_id).with_for_update())
            ).scalar_one_or_none()
            if not payment:
                webhook_event.status = WebhookEventStatus.IGNORED
                webhook_event.error_message = "payment not found"
                raise ValueError("Платеж не найден")

            to_status = PaymentStatus.SUCCESS if is_success else PaymentStatus.FAILED
            await PaymentService.transition_payment(
                db,
                payment,
                to_status,
                reason="provider_webhook",
                actor=ActorCtx(actor_type=PaymentActorType.WEBHOOK),
            )

            inv = (await db.execute(select(Investment).where(Investment.id == payment.investment_id).with_for_update())).scalar_one()
            if payment.status == PaymentStatus.SUCCESS:
                inv.status = InvestmentStatus.PAID
                inv.paid_at = datetime.now(timezone.utc)
            elif payment.status in {PaymentStatus.FAILED, PaymentStatus.CANCELED}:
                inv.status = InvestmentStatus.PENDING

            webhook_event.status = WebhookEventStatus.PROCESSED
            webhook_event.processed_at = datetime.now(timezone.utc)

        await db.refresh(payment)
        return payment

    @staticmethod
    async def handle_webhook(db: AsyncSession, data: PaymentWebhookData,
                             headers: Optional[Mapping[str, str]] = None) -> Payment:
        canonical_payload = {
            **data.payload,
            "provider_payment_id": data.provider_payment_id,  # <- обязательно
            "provider_event_id": data.provider_event_id,  # <- желательно
            "status": data.status,
            "event_type": data.event_type,
        }

        return await PaymentService.process_webhook(
            db,
            provider_payment_id=data.provider_payment_id,
            is_success=data.status == "success",
            provider_event_id=data.provider_event_id,
            payload=canonical_payload,
            headers=headers,
        )
    @staticmethod
    async def get_by_id(db: AsyncSession, payment_id: int) -> Optional[Payment]:
        query = select(Payment).where(Payment.id == payment_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
