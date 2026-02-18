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
