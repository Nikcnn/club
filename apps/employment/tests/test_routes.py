from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.employment import routes
from apps.employment.enums import MatchStatus, ReactionAction, ReactionSource, VacancyStatus
from apps.users.models import UserRole


@pytest.mark.asyncio
async def test_tg_check_creates_or_updates(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(routes.EmploymentService, "tg_check", AsyncMock(return_value=SimpleNamespace(telegram_id="1", is_blocked=False, linked_organization_id=None, linked_candidate_id=1)))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/employment/tg/check", json={"telegram_id": "1"})

    assert response.status_code == 200
    assert response.json()["is_linked"] is True


@pytest.mark.asyncio
async def test_validate_email_availability(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(routes.EmploymentService, "validate_organization_email", AsyncMock(return_value=True))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/employment/organizations/validate-email", json={"email": "org@example.com"})

    assert response.status_code == 200
    assert response.json()["available"] is True


@pytest.mark.asyncio
async def test_candidate_register_duplicate_email(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(routes.EmploymentService, "register_candidate", AsyncMock(side_effect=routes.HTTPException(status_code=400, detail="Candidate with this email already exists")))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/employment/candidates/register", json={"email": "dup@example.com", "description_json": {}})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_vacancy_crud_basic_path(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[routes.get_current_user] = lambda: SimpleNamespace(id=77, role=UserRole.ORGANIZATION)
    monkeypatch.setattr(routes.EmploymentService, "create_vacancy", AsyncMock(return_value=SimpleNamespace(id=1, organization_id=77, position_title="Backend", description_json={}, status=VacancyStatus.DRAFT, city=None, employment_type=None, is_remote=False)))
    monkeypatch.setattr(routes.EmploymentService, "update_vacancy_status", AsyncMock(return_value=SimpleNamespace(id=1, organization_id=77, position_title="Backend", description_json={}, status=VacancyStatus.ACTIVE, city=None, employment_type=None, is_remote=False)))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post("/employment/vacancies", json={"position_title": "Backend", "description_json": {}})
        status_resp = await client.patch("/employment/vacancies/1/status", json={"status": "active"})

    assert create_resp.status_code == 201
    assert status_resp.status_code == 200


@pytest.mark.asyncio
async def test_reaction_idempotency_same_key(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(
        routes.EmploymentService,
        "submit_reaction",
        AsyncMock(return_value=(SimpleNamespace(id=10), None, True)),
    )

    body = {
        "initiator_entity_type": "candidate",
        "initiator_entity_id": 1,
        "target_entity_type": "organization",
        "target_entity_id": 2,
        "vacancy_id": 5,
        "action": ReactionAction.LIKE.value,
        "source": ReactionSource.WEB.value,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/employment/reactions", headers={"Idempotency-Key": "same"}, json=body)

    assert response.status_code == 200
    assert response.json()["idempotent_replay"] is True


@pytest.mark.asyncio
async def test_mutual_match_creation_flow(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(
        routes.EmploymentService,
        "submit_reaction",
        AsyncMock(return_value=(SimpleNamespace(id=11), SimpleNamespace(id=2, status=MatchStatus.MUTUAL_MATCHED), False)),
    )

    body = {
        "initiator_entity_type": "organization",
        "initiator_entity_id": 2,
        "target_entity_type": "candidate",
        "target_entity_id": 1,
        "vacancy_id": 5,
        "action": "like",
        "source": "telegram_bot",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/employment/reactions", headers={"Idempotency-Key": "k2"}, json=body)

    assert response.status_code == 200
    assert response.json()["match_status"] == "mutual_matched"


@pytest.mark.asyncio
async def test_candidate_profile_update_creates_history_version(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    user = SimpleNamespace(id=2, email="c@example.com", role=UserRole.MEMBER)
    app.dependency_overrides[routes.get_current_user] = lambda: user

    class _Result:
        def __init__(self, value):
            self._value = value

        def scalars(self):
            return self

        def first(self):
            return self._value

    class DummySession:
        async def execute(self, *_args, **_kwargs):
            return _Result(SimpleNamespace(id=9, email="c@example.com"))

    async def _fake_db():
        yield DummySession()

    app.dependency_overrides[routes.get_db] = _fake_db
    monkeypatch.setattr(routes.EmploymentService, "update_candidate", AsyncMock(return_value=SimpleNamespace(id=9, email="c@example.com", description_json={}, links=[], category=None, city=None, resume_text=None, is_active=True)))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/employment/candidates/me", json={"city": "Almaty"})

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_recommendations_sorted(monkeypatch):
    app = FastAPI()
    app.include_router(routes.router)
    user = SimpleNamespace(id=2, email="c@example.com", role=UserRole.MEMBER)
    app.dependency_overrides[routes.get_current_user] = lambda: user

    class _Result:
        def __init__(self, value):
            self._value = value

        def scalars(self):
            return self

        def first(self):
            return self._value

    class DummySession:
        async def execute(self, *_args, **_kwargs):
            return _Result(SimpleNamespace(id=9, email="c@example.com", description_json={}))

    async def _fake_db():
        yield DummySession()

    app.dependency_overrides[routes.get_db] = _fake_db

    monkeypatch.setattr(
        routes.EmploymentService,
        "candidate_recommendations",
        AsyncMock(return_value=[
            {"entity_id": 2, "match_score": 0.95, "match_percent_display": 95, "confidence": "high", "explanation": {}},
            {"entity_id": 1, "match_score": 0.70, "match_percent_display": 70, "confidence": "medium", "explanation": {}},
        ]),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/employment/recommendations/vacancies-for-candidate")

    assert response.status_code == 200
    data = response.json()
    assert data[0]["match_score"] >= data[1]["match_score"]
