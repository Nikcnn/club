from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from fastadmin import fastapi_app as fastapi_admin_app

from apps.admin.auth import admin_basic_auth


async def _build_dashboard_payload() -> dict[str, Any]:
    return {
        "title": "ClubVerse Admin Dashboard",
        "widgets": [
            {"name": "users", "label": "Пользователи", "value": None},
            {"name": "clubs", "label": "Клубы", "value": None},
            {"name": "campaigns", "label": "Кампании", "value": None},
            {"name": "payments", "label": "Платежи", "value": None},
        ],
    }


def setup_admin(app: FastAPI) -> None:
    """Инициализация fastapi-admin + защищённый dashboard endpoint."""

    # Подключаем fastapi-admin под /admin
    app.mount("/admin", fastapi_admin_app)

    @app.get("/admin-dashboard", tags=["admin"])
    async def admin_dashboard(_: str = Depends(admin_basic_auth)) -> JSONResponse:
        payload = await _build_dashboard_payload()
        payload["meta"] = {
            "note": "Дашборд для админки. Добавьте агрегаты из БД в _build_dashboard_payload().",
        }
        return JSONResponse(payload)
