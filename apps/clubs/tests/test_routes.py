from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.clubs import routes
from apps.users.models import UserRole


@pytest.mark.asyncio
async def test_list_clubs_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(
        routes.ClubService,
        "get_all",
        AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "name": "Club One",
                    "category": "IT",
                    "city": "Almaty",
                    "description": None,
                    "website": None,
                    "social_links": {},
                    "email": "club@example.com",
                    "logo_key": None,
                }
            ]
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/clubs/")

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Club One"


@pytest.mark.asyncio
async def test_update_club_forbidden_for_non_club_role():
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[routes.get_current_user] = lambda: SimpleNamespace(id=1, role=UserRole.MEMBER)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/clubs/me", json={"name": "New Name"})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_club_logo_forbidden_for_non_club_role():
    app = FastAPI()
    app.include_router(routes.router)

    async def _fake_db():
        yield None

    app.dependency_overrides[routes.get_db] = _fake_db
    app.dependency_overrides[routes.get_current_user] = lambda: SimpleNamespace(id=1, role=UserRole.MEMBER)

    files = {"logo": ("logo.png", b"fake-image-bytes", "image/png")}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/clubs/me/logo", files=files)

    assert response.status_code == 403
