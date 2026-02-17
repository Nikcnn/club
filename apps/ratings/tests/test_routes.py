from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.ratings import routes


@pytest.mark.asyncio
async def test_get_club_rating_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    monkeypatch.setattr(
        routes.RatingService,
        "get_club_rating",
        AsyncMock(return_value={"avg_score": "4.50", "review_count": 12}),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ratings/club/1")

    assert response.status_code == 200
    assert response.json()["review_count"] == 12
