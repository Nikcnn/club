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


@pytest.mark.asyncio
async def test_upload_my_avatar_uses_user_from_current_session(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    detached_user = SimpleNamespace(id=9, email="detached@example.com", avatar_key=None, role=UserRole.MEMBER, is_active=True)
    persistent_user = SimpleNamespace(
        id=9,
        email="db@example.com",
        avatar_key=None,
        role=UserRole.MEMBER,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    class DummySession:
        def __init__(self):
            self.refresh_arg = None
            self.committed = False

        async def commit(self):
            self.committed = True

        async def refresh(self, obj):
            self.refresh_arg = obj

    db = DummySession()

    async def _fake_db():
        yield db

    app.dependency_overrides[routes.get_db] = _fake_db
    app.dependency_overrides[routes.get_current_user] = lambda: detached_user

    monkeypatch.setattr(routes, "upload_image_to_minio", AsyncMock(return_value="users/9/avatar.png"))
    monkeypatch.setattr(routes.UserService, "get_by_id", AsyncMock(return_value=persistent_user))

    files = {"avatar": ("avatar.png", b"fake-image-bytes", "image/png")}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/users/me/avatar", files=files)

    assert response.status_code == 200
    assert db.committed is True
    assert db.refresh_arg is persistent_user
    assert persistent_user.avatar_key == "users/9/avatar.png"


@pytest.mark.asyncio
async def test_upload_my_avatar_returns_404_when_user_not_found(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    detached_user = SimpleNamespace(id=9, email="detached@example.com", avatar_key=None, role=UserRole.MEMBER, is_active=True)

    class DummySession:
        async def commit(self):
            raise AssertionError("commit should not be called")

        async def refresh(self, obj):
            raise AssertionError("refresh should not be called")

    db = DummySession()

    async def _fake_db():
        yield db

    app.dependency_overrides[routes.get_db] = _fake_db
    app.dependency_overrides[routes.get_current_user] = lambda: detached_user

    monkeypatch.setattr(routes, "upload_image_to_minio", AsyncMock(return_value="users/9/avatar.png"))
    monkeypatch.setattr(routes.UserService, "get_by_id", AsyncMock(return_value=None))

    files = {"avatar": ("avatar.png", b"fake-image-bytes", "image/png")}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/users/me/avatar", files=files)

    assert response.status_code == 404
