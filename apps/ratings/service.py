from typing import Optional
from decimal import Decimal
from sqlalchemy import select, func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.ratings.models import ClubRating, OrganizationRating
from apps.reviews.models import ClubReview, OrganizationReview


class RatingService:

    # ==========================
    # CLUB RATING
    # ==========================

    @staticmethod
    async def get_club_rating(db: AsyncSession, club_id: int) -> ClubRating:
        """
        Получает рейтинг. Если записи нет — возвращает "пустой" объект (0.0, 0 отзывов).
        """
        query = select(ClubRating).where(ClubRating.club_id == club_id)
        result = await db.execute(query)
        rating = result.scalar_one_or_none()

        if not rating:
            # Возвращаем временный объект, чтобы не ломать фронтенд
            return ClubRating(club_id=club_id, avg_score=Decimal(0), review_count=0)

        return rating

    @staticmethod
    async def recalculate_club_rating(db: AsyncSession, club_id: int) -> ClubRating:
        """
        Пересчитывает рейтинг на основе таблицы club_reviews.
        Вызывается после добавления нового отзыва.
        """
        # 1. Считаем агрегацию из отзывов
        stmt = select(
            func.count(ClubReview.id).label("count"),
            func.avg(ClubReview.score).label("avg")
        ).where(ClubReview.club_id == club_id)

        result = await db.execute(stmt)
        stats = result.one()

        new_count = stats.count
        # Если отзывов нет, avg вернет None, заменяем на 0
        new_avg = stats.avg if stats.avg is not None else 0

        # 2. Upsert (Обновляем или Создаем запись рейтинга)
        # Для PostgreSQL используем insert().on_conflict_do_update()
        stmt = insert(ClubRating).values(
            club_id=club_id,
            avg_score=new_avg,
            review_count=new_count
        ).on_conflict_do_update(
            index_elements=['club_id'],
            set_={
                "avg_score": new_avg,
                "review_count": new_count,
                "updated_at": func.now()
            }
        ).returning(ClubRating)

        result = await db.execute(stmt)
        await db.commit()
        updated_rating = result.scalar_one()

        return updated_rating

    # ==========================
    # ORGANIZATION RATING
    # ==========================

    @staticmethod
    async def get_org_rating(db: AsyncSession, org_id: int) -> OrganizationRating:
        query = select(OrganizationRating).where(OrganizationRating.organization_id == org_id)
        result = await db.execute(query)
        rating = result.scalar_one_or_none()

        if not rating:
            return OrganizationRating(organization_id=org_id, avg_score=Decimal(0), review_count=0)

        return rating

    @staticmethod
    async def recalculate_org_rating(db: AsyncSession, org_id: int) -> OrganizationRating:
        stmt = select(
            func.count(OrganizationReview.id),
            func.avg(OrganizationReview.score)
        ).where(OrganizationReview.organization_id == org_id)

        result = await db.execute(stmt)
        count, avg = result.one()

        new_avg = avg if avg is not None else 0

        stmt = insert(OrganizationRating).values(
            organization_id=org_id,
            avg_score=new_avg,
            review_count=count
        ).on_conflict_do_update(
            index_elements=['organization_id'],
            set_={"avg_score": new_avg, "review_count": count, "updated_at": func.now()}
        ).returning(OrganizationRating)

        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one()