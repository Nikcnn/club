from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.users import routes
from apps.users.models import UserRole


@pytest.mark.asyncio
async def test_register_member_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    monkeypatch.setattr(routes.UserService, "get_by_email", AsyncMock(return_value=None))
    monkeypatch.setattr(
        routes.UserService,
        "create_member",
        AsyncMock(
            return_value={
                "id": 1,
                "email": "user@example.com",
                "avatar_key": None,
                "role": UserRole.MEMBER,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/users/register",
            json={"email": "user@example.com", "password": "secret123", "avatar_key": None},
        )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_read_me_success():
    app = FastAPI()
    app.include_router(routes.router)

    test_user = SimpleNamespace(
        id=9,
        email="me@example.com",
        avatar_key=None,
        role=UserRole.MEMBER,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    app.dependency_overrides[routes.get_current_user] = lambda: test_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users/me")

    assert response.status_code == 200
    assert response.json()["id"] == 9
