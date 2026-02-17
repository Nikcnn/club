from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.funding import routes


@pytest.mark.asyncio
async def test_list_campaigns_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    monkeypatch.setattr(
        routes.CampaignService,
        "get_all",
        AsyncMock(
            return_value=[
                {
                    "id": 3,
                    "club_id": 1,
                    "title": "Support club",
                    "description": "Campaign",
                    "goal_amount": "1000.00",
                    "starts_at": datetime.now(timezone.utc).isoformat(),
                    "ends_at": datetime.now(timezone.utc).isoformat(),
                    "cover_key": None,
                    "gallery_keys": [],
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": None,
                    "current_amount": "0.00",
                }
            ]
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/funding/campaigns/")

    assert response.status_code == 200
    assert response.json()[0]["id"] == 3
