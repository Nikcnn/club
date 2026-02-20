from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.moderation.service import ModerationService
from apps.ratings.service import RatingService
from apps.reviews.models import ClubReview, OrganizationReview
from apps.reviews.schemas import ReviewCreate


class ReviewService:
    @staticmethod
    async def add_club_review(db: AsyncSession, schema: ReviewCreate, user_id: int, club_id: int):
        query = select(ClubReview).where(
            ClubReview.user_id == user_id,
            ClubReview.club_id == club_id,
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Вы уже оставили отзыв этому клубу.")

        toxicity, labels = await ModerationService.analyze_text(schema.text)
        moderation_status, is_approved = ModerationService.decide_status(toxicity)

        review = ClubReview(
            user_id=user_id,
            club_id=club_id,
            text=schema.text,
            score=schema.score,
            toxicity_score=toxicity,
            moderation_labels=labels,
            moderation_status=moderation_status,
            is_approved=is_approved,
        )
        db.add(review)

        await db.commit()
        await db.refresh(review)

        if review.is_approved:
            await RatingService.recalculate_club_rating(db, club_id)

        return review

    @staticmethod
    async def add_org_review(db: AsyncSession, schema: ReviewCreate, user_id: int, org_id: int):
        query = select(OrganizationReview).where(
            OrganizationReview.user_id == user_id,
            OrganizationReview.organization_id == org_id,
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Вы уже оставили отзыв этому организатору.")

        toxicity, labels = await ModerationService.analyze_text(schema.text)
        moderation_status, is_approved = ModerationService.decide_status(toxicity)

        review = OrganizationReview(
            user_id=user_id,
            organization_id=org_id,
            text=schema.text,
            score=schema.score,
            toxicity_score=toxicity,
            moderation_labels=labels,
            moderation_status=moderation_status,
            is_approved=is_approved,
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)

        if review.is_approved:
            await RatingService.recalculate_org_rating(db, org_id)

        return review

    @staticmethod
    async def list_club_reviews(db: AsyncSession, club_id: int) -> list[ClubReview]:
        result = await db.execute(
            select(ClubReview).where(ClubReview.club_id == club_id, ClubReview.is_approved.is_(True))
        )
        return result.scalars().all()

    @staticmethod
    async def list_org_reviews(db: AsyncSession, org_id: int) -> list[OrganizationReview]:
        result = await db.execute(
            select(OrganizationReview).where(
                OrganizationReview.organization_id == org_id,
                OrganizationReview.is_approved.is_(True),
            )
        )
        return result.scalars().all()
