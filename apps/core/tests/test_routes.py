import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.core import routes


@pytest.mark.asyncio
async def test_get_public_media_url(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)

    monkeypatch.setattr(routes, "build_public_url", lambda key: f"https://cdn.test/public/{key}")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/media/public-url", params={"object_key": "users/1/avatar.png"})

    assert response.status_code == 200
    assert response.json() == {
        "object_key": "users/1/avatar.png",
        "url": "https://cdn.test/public/users/1/avatar.png",
    }
