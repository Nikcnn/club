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
