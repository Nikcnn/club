from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.organizations import routes


@pytest.mark.asyncio
async def test_list_organizations_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(
        routes.OrganizationService,
        "get_all",
        AsyncMock(
            return_value=[
                {
                    "id": 2,
                    "name": "Org",
                    "city": "Astana",
                    "description": "desc",
                    "website": None,
                    "logo_key": None,
                    "email": "org@example.com",
                    "role": "organization",
                    "is_active": True,
                }
            ]
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/organizations/")

    assert response.status_code == 200
    assert response.json()[0]["email"] == "org@example.com"
