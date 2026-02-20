from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.reviews import routes


@pytest.mark.asyncio
async def test_review_club_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    app.dependency_overrides[routes.get_current_user] = lambda: SimpleNamespace(id=3)
    monkeypatch.setattr(
        routes.ReviewService,
        "add_club_review",
        Mock(
            return_value={
                "id": 1,
                "text": "Great",
                "score": 5,
                "user_id": 3,
                "is_approved": True,
                "moderation_status": "APPROVED",
                "toxicity_score": 0.1,
                "created_at": "2025-01-01T00:00:00",
            }
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/reviews/club/1", json={"text": "Great", "score": 5})

    assert response.status_code == 200
    assert response.json()["score"] == 5


@pytest.mark.asyncio
async def test_public_list_returns_only_approved(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    monkeypatch.setattr(
        routes.ReviewService,
        "list_club_reviews",
        AsyncMock(
            return_value=[
                {
                    "id": 2,
                    "text": "Nice",
                    "score": 4,
                    "user_id": 7,
                    "is_approved": True,
                    "moderation_status": "APPROVED",
                    "toxicity_score": 0.01,
                    "created_at": "2025-01-01T00:00:00",
                }
            ]
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/reviews/club/1")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 2,
            "text": "Nice",
            "score": 4,
            "user_id": 7,
            "is_approved": True,
            "moderation_status": "APPROVED",
            "toxicity_score": 0.01,
            "created_at": "2025-01-01T00:00:00",
        }
    ]
