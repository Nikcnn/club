from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.payments import routes


@pytest.mark.asyncio
async def test_initiate_payment_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[routes.get_current_user] = lambda: SimpleNamespace(id=15)

    monkeypatch.setattr(
        routes.PaymentService,
        "initiate_payment",
        AsyncMock(
            return_value={
                "id": 5,
                "investment_id": 7,
                "amount": "100.00",
                "status": "pending",
                "provider": "paybox",
                "checkout_url": "https://pay.local",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "confirmed_at": None,
            }
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/payments/initiate", json={"investment_id": 7, "provider": "paybox"})

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
