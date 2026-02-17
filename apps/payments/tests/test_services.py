from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.funding.models import InvestmentStatus
from apps.payments.models import PaymentProvider, PaymentStatus
from apps.payments.schemas import PaymentInitiate
from apps.payments.services import PaymentService


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


@pytest.mark.asyncio
async def test_initiate_payment_returns_existing_by_idempotency_key():
    investment = SimpleNamespace(id=7, investor_id=15, status=InvestmentStatus.PENDING, amount=100)
    existing_payment = SimpleNamespace(investment_id=7, provider=PaymentProvider.PAYBOX)

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_Result(investment), _Result(existing_payment)])

    payment = await PaymentService.initiate_payment(
        db,
        PaymentInitiate(investment_id=7, provider=PaymentProvider.PAYBOX),
        user_id=15,
        idempotency_key="retry-key",
    )

    assert payment is existing_payment
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_initiate_payment_reuses_existing_pending_payment_for_investment():
    investment = SimpleNamespace(id=7, investor_id=15, status=InvestmentStatus.PENDING, amount=100)
    existing_payment = SimpleNamespace(
        investment_id=7,
        provider=PaymentProvider.PAYBOX,
        status=PaymentStatus.PENDING,
        idempotency_key=None,
    )

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_Result(investment), _Result(existing_payment)])

    payment = await PaymentService.initiate_payment(
        db,
        PaymentInitiate(investment_id=7, provider=PaymentProvider.PAYBOX),
        user_id=15,
    )

    assert payment is existing_payment
    db.commit.assert_not_awaited()
