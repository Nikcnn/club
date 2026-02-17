from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from apps.news.models import News
from apps.news.schemas import NewsCreate, NewsUpdate


class NewsService:
    @staticmethod
    async def create(db: AsyncSession, schema: NewsCreate, club_id: int) -> News:
        news = News(
            **schema.model_dump(),
            club_id=club_id,
            published_at=datetime.utcnow() if schema.is_published else None
        )
        db.add(news)
        await db.commit()
        await db.refresh(news)
        return news

    @staticmethod
    async def get_all(
        db: AsyncSession,
        club_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[News]:
        query = select(News)

        if club_id:
            query = query.where(News.club_id == club_id)

        # Сортировка: сначала свежие
        query = query.order_by(desc(News.created_at)).offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, news_id: int) -> Optional[News]:
        query = select(News).where(News.id == news_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        news_id: int,
        schema: NewsUpdate
    ) -> Optional[News]:
        news = await NewsService.get_by_id(db, news_id)
        if not news:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(news, key, value)

        await db.commit()
        await db.refresh(news)
        return news

    @staticmethod
    async def delete(db: AsyncSession, news_id: int) -> bool:
        news = await NewsService.get_by_id(db, news_id)
        if not news:
            return False

        await db.delete(news)
        await db.commit()
        return True