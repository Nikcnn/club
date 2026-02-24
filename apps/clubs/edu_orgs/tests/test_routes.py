from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.clubs.edu_orgs import routes


@pytest.mark.asyncio
async def test_create_educational_organization_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    monkeypatch.setattr(
        routes.EduOrgService,
        "create",
        AsyncMock(
            return_value={
                "id": 1,
                "name": "NIS",
                "city": "Almaty",
                "description": None,
                "departments": ["IT"],
                "logo_key": None,
                "website": None,
                "social_links": {},
            }
        ),
    )

    payload = {
        "name": "NIS",
        "city": "Almaty",
        "departments": ["IT"],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/educational-organizations/", json=payload)

    assert response.status_code == 201
    assert response.json()["name"] == "NIS"


@pytest.mark.asyncio
async def test_get_educational_organization_not_found(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    monkeypatch.setattr(routes.EduOrgService, "get_by_id", AsyncMock(return_value=None))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/educational-organizations/99")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_educational_organization_logo_success(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    edu_org = type(
        "E",
        (),
        {
            "id": 1,
            "name": "NIS",
            "city": "Almaty",
            "description": None,
            "departments": ["IT"],
            "logo_key": None,
            "website": None,
            "social_links": {},
        },
    )()

    monkeypatch.setattr(routes.EduOrgService, "get_by_id", AsyncMock(return_value=edu_org))
    monkeypatch.setattr(
        routes,
        "upload_image_to_minio",
        AsyncMock(return_value="educational-organizations/1/logo.png"),
    )

    db = AsyncMock()
    app.dependency_overrides[routes.get_db] = lambda: db

    files = {"logo": ("logo.png", b"fake-image-bytes", "image/png")}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/educational-organizations/1/logo", files=files)

    assert response.status_code == 200
    assert response.json()["logo_key"] == "educational-organizations/1/logo.png"
