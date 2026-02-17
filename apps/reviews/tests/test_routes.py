from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.reviews import routes


@pytest.mark.asyncio
async def test_review_club_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    app.dependency_overrides[routes.get_current_user] = lambda: type("User", (), {"id": 3})()
    monkeypatch.setattr(
        routes.ReviewService,
        "add_club_review",
        Mock(return_value={"id": 1, "text": "Great", "score": 5, "user_id": 3, "created_at": "2025-01-01"}),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/reviews/club/1", json={"text": "Great", "score": 5})

    assert response.status_code == 200
    assert response.json()["score"] == 5
