from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.news import routes


@pytest.mark.asyncio
async def test_list_news_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    monkeypatch.setattr(
        routes.NewsService,
        "get_all",
        AsyncMock(
            return_value=[
                {
                    "id": 22,
                    "club_id": 1,
                    "title": "News",
                    "body": "Body",
                    "cover_key": None,
                    "is_published": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": None,
                    "published_at": None,
                }
            ]
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/news/")

    assert response.status_code == 200
    assert response.json()[0]["id"] == 22


@pytest.mark.asyncio
async def test_upload_news_cover_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    current_user = type("U", (), {"id": 7})()
    app.dependency_overrides[routes.get_current_user] = lambda: current_user

    news = type(
        "N",
        (),
        {
            "id": 22,
            "club_id": 7,
            "title": "News",
            "body": "Body",
            "cover_key": None,
            "is_published": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": None,
            "published_at": None,
        },
    )()

    monkeypatch.setattr(routes.NewsService, "get_by_id", AsyncMock(return_value=news))
    monkeypatch.setattr(routes, "upload_image_to_minio", AsyncMock(return_value="news/22/cover.png"))

    db = AsyncMock()
    app.dependency_overrides[routes.get_db] = lambda: db

    files = {"cover": ("cover.png", b"fake-image-bytes", "image/png")}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/news/22/cover", files=files)

    assert response.status_code == 200
    assert response.json()["cover_key"] == "news/22/cover.png"


@pytest.mark.asyncio
async def test_upload_news_cover_forbidden(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    current_user = type("U", (), {"id": 9})()
    app.dependency_overrides[routes.get_current_user] = lambda: current_user

    news = type(
        "N",
        (),
        {
            "id": 22,
            "club_id": 7,
            "title": "News",
            "body": "Body",
            "cover_key": None,
            "is_published": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": None,
            "published_at": None,
        },
    )()

    monkeypatch.setattr(routes.NewsService, "get_by_id", AsyncMock(return_value=news))
    db = AsyncMock()
    app.dependency_overrides[routes.get_db] = lambda: db

    files = {"cover": ("cover.png", b"fake-image-bytes", "image/png")}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/news/22/cover", files=files)

    assert response.status_code == 403
