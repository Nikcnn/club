from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apps.reviews.models import ClubReview, OrganizationReview
from apps.reviews.schemas import ReviewCreate
from apps.ratings.service import RatingService

class ReviewService:
    @staticmethod
    async def add_club_review(db: AsyncSession, schema: ReviewCreate, user_id: int, club_id: int):
        # 1. Проверка: не оставлял ли уже отзыв
        query = select(ClubReview).where(
            ClubReview.user_id == user_id,
            ClubReview.club_id == club_id
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("Вы уже оставили отзыв этому клубу.")

        # 2. Создаем отзыв
        review = ClubReview(
            user_id=user_id,
            club_id=club_id,
            text=schema.text,
            score=schema.score
        )
        db.add(review)

        # 3. ВАЖНО: await commit и refresh
        await db.commit()
        await db.refresh(review)
        await RatingService.recalculate_club_rating(db, club_id)

        return review

    @staticmethod
    async  def add_org_review(db: AsyncSession, schema: ReviewCreate, user_id: int, org_id: int):
        review = OrganizationReview(
            user_id=user_id,
            organization_id=org_id,
            text=schema.text,
            score=schema.score
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        await RatingService.recalculate_org_rating(db, org_id)

        return review