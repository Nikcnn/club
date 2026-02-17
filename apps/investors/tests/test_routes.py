from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.investors import routes


@pytest.mark.asyncio
async def test_register_investor_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    monkeypatch.setattr(routes.UserService, "get_by_email", AsyncMock(return_value=None))
    monkeypatch.setattr(
        routes.InvestorService,
        "create",
        AsyncMock(
            return_value={
                "id": 10,
                "email": "investor@example.com",
                "role": "investor",
                "is_active": True,
                "bio": None,
                "company_name": None,
                "linkedin_url": None,
                "avatar_key": None,
            }
        ),
    )

    payload = {"email": "investor@example.com", "password": "secret123", "bio": "Bio"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/investors/register", json=payload)

    assert response.status_code == 201
    assert response.json()["id"] == 10
