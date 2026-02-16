from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from apps.reviews.models import ClubReview, OrganizationReview
from apps.reviews.schemas import ReviewCreate

class ReviewService:
    # ==========================
    # Club Reviews
    # ==========================
    @staticmethod
    async def get_club_reviews(
        db: AsyncSession,
        club_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[ClubReview]:
        query = select(ClubReview).where(ClubReview.club_id == club_id)
        query = query.order_by(desc(ClubReview.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def add_club_review(
        db: AsyncSession,
        schema: ReviewCreate,
        user_id: int,
        club_id: int
    ) -> ClubReview:
        # Проверка на дубликат
        query = select(ClubReview).where(
            ClubReview.club_id == club_id,
            ClubReview.user_id == user_id
        )
        existing = await db.execute(query)
        if existing.scalar_one_or_none():
            raise ValueError("Вы уже оставили отзыв этому клубу.")

        review = ClubReview(
            user_id=user_id,
            club_id=club_id,
            text=schema.text,
            score=schema.score
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        await RatingService.recalculate_club_rating(db, club_id)
        return review

    # ==========================
    # Organization Reviews
    # ==========================
    @staticmethod
    async def get_org_reviews(
        db: AsyncSession,
        org_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[OrganizationReview]:
        query = select(OrganizationReview).where(OrganizationReview.organization_id == org_id)
        query = query.order_by(desc(OrganizationReview.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def add_org_review(
        db: AsyncSession,
        schema: ReviewCreate,
        user_id: int,
        org_id: int
    ) -> OrganizationReview:
        # Проверка на дубликат
        query = select(OrganizationReview).where(
            OrganizationReview.organization_id == org_id,
            OrganizationReview.user_id == user_id
        )
        existing = await db.execute(query)
        if existing.scalar_one_or_none():
            raise ValueError("Вы уже оставили отзыв этой организации.")

        review = OrganizationReview(
            user_id=user_id,
            organization_id=org_id,
            text=schema.text,
            score=schema.score
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review