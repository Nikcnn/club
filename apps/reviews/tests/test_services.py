from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from apps.reviews.schemas import ReviewCreate
from apps.reviews.services import ReviewService


class _NoReviewResult:
    @staticmethod
    def scalar_one_or_none():
        return None


class FakeDB:
    def __init__(self):
        self.added = None
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _NoReviewResult()

    def add(self, obj):
        self.added = obj

    async def commit(self):
        return None

    async def refresh(self, _obj):
        return None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("toxicity", "expected_status", "expected_approved"),
    [
        (0.3, "APPROVED", True),
        (0.6, "PENDING", False),
        (0.9, "REJECTED", False),
    ],
)
async def test_add_club_review_sets_moderation(monkeypatch, toxicity, expected_status, expected_approved):
    db = FakeDB()

    monkeypatch.setattr(
        "apps.reviews.services.ModerationService.analyze_text",
        AsyncMock(return_value=(toxicity, {"TOXICITY": toxicity})),
    )
    recalculate_mock = AsyncMock()
    monkeypatch.setattr("apps.reviews.services.RatingService.recalculate_club_rating", recalculate_mock)

    schema = ReviewCreate(text="text", score=5)
    review = await ReviewService.add_club_review(db, schema, user_id=10, club_id=22)

    assert review.moderation_status == expected_status
    assert review.is_approved is expected_approved
    assert review.toxicity_score == toxicity

    if expected_approved:
        recalculate_mock.assert_awaited_once_with(db, 22)
    else:
        recalculate_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_public_list_query_filters_only_approved():
    class Result:
        @staticmethod
        def scalars():
            return SimpleNamespace(all=lambda: [])

    class DB:
        def __init__(self):
            self.statement = None

        async def execute(self, statement):
            self.statement = statement
            return Result()

    db = DB()
    await ReviewService.list_club_reviews(db, 1)

    sql = str(db.statement)
    assert "club_reviews.is_approved" in sql


@pytest.mark.asyncio
async def test_org_rating_recalculate_only_for_approved(monkeypatch):
    db = FakeDB()

    monkeypatch.setattr(
        "apps.reviews.services.ModerationService.analyze_text",
        AsyncMock(return_value=(0.55, {"TOXICITY": 0.55})),
    )
    recalculate_mock = AsyncMock()
    monkeypatch.setattr("apps.reviews.services.RatingService.recalculate_org_rating", recalculate_mock)

    schema = ReviewCreate(text="text", score=3)
    review = await ReviewService.add_org_review(db, schema, user_id=10, org_id=33)

    assert review.moderation_status == "PENDING"
    recalculate_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_local_blocklist_rejects_even_without_provider(monkeypatch):
    db = FakeDB()

    monkeypatch.setattr("apps.moderation.service.settings.MODERATION_ENABLED", True, raising=False)
    monkeypatch.setattr("apps.moderation.service.settings.PERSPECTIVE_API_KEY", None, raising=False)

    recalculate_mock = AsyncMock()
    monkeypatch.setattr("apps.reviews.services.RatingService.recalculate_club_rating", recalculate_mock)

    schema = ReviewCreate(text="fagot", score=1)
    review = await ReviewService.add_club_review(db, schema, user_id=7, club_id=7)

    assert review.moderation_status == "REJECTED"
    assert review.is_approved is False
    assert review.toxicity_score >= 0.9
    recalculate_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_provider_healthcheck_returns_error_message(monkeypatch):
    from apps.moderation.service import ModerationService

    monkeypatch.setattr("apps.moderation.service.settings.MODERATION_ENABLED", True, raising=False)
    monkeypatch.setattr("apps.moderation.service.settings.MODERATION_PROVIDER", "perspective", raising=False)
    monkeypatch.setattr("apps.moderation.service.settings.PERSPECTIVE_API_KEY", "key", raising=False)

    class Response:
        status_code = 403
        text = "forbidden"

        @staticmethod
        def json():
            return {"error": {"message": "API key not valid"}}

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr("apps.moderation.service.httpx.AsyncClient", lambda timeout: Client())

    result = await ModerationService.provider_healthcheck()
    assert result["ok"] is False
    assert result["http_status"] == 403
    assert result["error"] == "API key not valid"


@pytest.mark.asyncio
async def test_provider_healthcheck_gemini_missing_key(monkeypatch):
    from apps.moderation.service import ModerationService

    monkeypatch.setattr("apps.moderation.service.settings.MODERATION_ENABLED", True, raising=False)
    monkeypatch.setattr("apps.moderation.service.settings.MODERATION_PROVIDER", "gemini", raising=False)
    monkeypatch.setattr("apps.moderation.service.settings.GEMINI_API_KEY", None, raising=False)

    result = await ModerationService.provider_healthcheck()
    assert result == {"ok": False, "state": "missing_api_key", "provider": "gemini"}
