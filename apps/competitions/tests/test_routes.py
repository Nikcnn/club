from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.competitions import routes


@pytest.mark.asyncio
async def test_list_competitions_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    start = datetime.now(timezone.utc)
    end = start + timedelta(days=1)
    monkeypatch.setattr(
        routes.CompetitionService,
        "get_all",
        AsyncMock(
            return_value=[
                {
                    "id": 11,
                    "club_id": 1,
                    "title": "Hackathon",
                    "description": "desc",
                    "starts_at": start.isoformat(),
                    "ends_at": end.isoformat(),
                    "photo_key": None,
                    "status": "draft",
                    "created_at": start.isoformat(),
                    "updated_at": None,
                }
            ]
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/competitions/")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Hackathon"
