import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.funding.models import Investment, InvestmentStatus
from apps.payments.models import Payment, PaymentProvider, PaymentStatus
from apps.payments.schemas import PaymentInitiate


class PaymentService:

    @staticmethod
    async def initiate_payment(
        db: AsyncSession,
        schema: PaymentInitiate,
        user_id: int,
        idempotency_key: Optional[str] = None
    ) -> Payment:
        """
        Создание платежа и генерация ссылки.
        """
        # 1. Проверяем инвестицию
        query = select(Investment).where(Investment.id == schema.investment_id)
        result = await db.execute(query)
        investment = result.scalar_one_or_none()

        if not investment:
            raise ValueError("Инвестиция не найдена")

        if investment.investor_id != user_id:
            raise ValueError("Вы не можете оплатить чужую инвестицию")

        if investment.status == InvestmentStatus.PAID:
            raise ValueError("Эта инвестиция уже оплачена")

        # 2. Если передан idempotency key и мы уже выполняли такой запрос —
        # возвращаем ранее созданный платеж без повторной инициации.
        if idempotency_key:
            idempotent_payment_q = select(Payment).where(Payment.idempotency_key == idempotency_key)
            idempotent_payment = (await db.execute(idempotent_payment_q)).scalar_one_or_none()
            if idempotent_payment:
                if idempotent_payment.investment_id != investment.id:
                    raise ValueError("Idempotency ключ уже использован для другой инвестиции")
                if idempotent_payment.provider != schema.provider:
                    raise ValueError("Idempotency ключ уже использован с другим провайдером")
                return idempotent_payment

        # 3. Проверяем, нет ли уже активного платежа (чтобы не дублировать)
        existing_payment_q = select(Payment).where(Payment.investment_id == investment.id)
        existing_payment = (await db.execute(existing_payment_q)).scalar_one_or_none()

        if existing_payment and existing_payment.status == PaymentStatus.SUCCESS:
            raise ValueError("Платеж уже прошел успешно")

        if existing_payment and existing_payment.status == PaymentStatus.PENDING:
            if idempotency_key and existing_payment.idempotency_key and existing_payment.idempotency_key != idempotency_key:
                raise ValueError("Для этой инвестиции уже есть активный платеж с другим idempotency ключом")
            if idempotency_key and not existing_payment.idempotency_key:
                existing_payment.idempotency_key = idempotency_key
                await db.commit()
                await db.refresh(existing_payment)
            return existing_payment

        # 4. Имитация запроса к платежной системе (получение ID транзакции)
        provider_id = str(uuid.uuid4())  # ID от PayBox
        checkout_url = f"https://paybox.money/pay/{provider_id}"  # Ссылка на форму

        # 5. Создаем или обновляем запись о платеже
        if existing_payment:
            payment = existing_payment
            payment.provider_payment_id = provider_id
            payment.checkout_url = checkout_url
            payment.status = PaymentStatus.PENDING
            if idempotency_key:
                payment.idempotency_key = idempotency_key
        else:
            payment = Payment(
                investment_id=investment.id,
                amount=investment.amount,  # Берем сумму строго из инвестиции!
                provider=schema.provider,
                provider_payment_id=provider_id,
                idempotency_key=idempotency_key,
                checkout_url=checkout_url,
                status=PaymentStatus.PENDING
            )
            db.add(payment)

        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def process_webhook(
        db: AsyncSession,
        provider_payment_id: str,
        is_success: bool
    ) -> Payment:
        """
        Обработка колбэка от платежной системы.
        """
        # 1. Ищем платеж по ID из внешней системы
        query = select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        result = await db.execute(query)
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError("Платеж не найден")

        if payment.status == PaymentStatus.SUCCESS:
            return payment  # Уже обработан

        # 2. Обновляем статус платежа
        if is_success:
            payment.status = PaymentStatus.SUCCESS
            payment.confirmed_at = datetime.utcnow()

            # 3. ВАЖНО: Обновляем статус самой инвестиции
            # Подгружаем investment, если он не в сессии
            inv_query = select(Investment).where(Investment.id == payment.investment_id)
            inv_result = await db.execute(inv_query)
            investment = inv_result.scalar_one()

            investment.status = InvestmentStatus.PAID
            investment.paid_at = datetime.utcnow()

        else:
            payment.status = PaymentStatus.FAILED

        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def get_by_id(db: AsyncSession, payment_id: int) -> Optional[Payment]:
        query = select(Payment).where(Payment.id == payment_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()