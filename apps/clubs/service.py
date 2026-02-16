from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_
from passlib.context import CryptContext

from apps.clubs.models import Club
from apps.clubs.schemas import ClubCreate, ClubUpdate
from apps.users.models import UserRole

# Настройка хеширования (обычно выносится в core.security)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ClubService:
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    async def create(db: AsyncSession, schema: ClubCreate) -> Club:
        # 1. Хешируем пароль
        hashed_pw = ClubService.get_password_hash(schema.password)

        # 2. Создаем объект (SQLAlchemy сам разберется, что часть полей идет в users, часть в clubs)
        club = Club(
            email=schema.email,
            password_hash=hashed_pw,  # Поле из модели User
            role=UserRole.CLUB,  # Принудительно ставим роль

            name=schema.name,
            category=schema.category,
            city=schema.city,
            description=schema.description,
            website=schema.website,
            social_links=schema.social_links
        )

        db.add(club)
        await db.commit()
        await db.refresh(club)
        return club

    @staticmethod
    async def get_by_id(db: AsyncSession, club_id: int) -> Optional[Club]:
        query = select(Club).where(Club.id == club_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        city: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Club]:
        """
        Умный поиск с фильтрами
        """
        query = select(Club)

        if city:
            query = query.where(Club.city == city)
        if category:
            query = query.where(Club.category == category)
        if search:
            # Поиск по имени или описанию (Case Insensitive)
            query = query.where(
                or_(
                    Club.name.ilike(f"%{search}%"),
                    Club.description.ilike(f"%{search}%")
                )
            )

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, club: Club, schema: ClubUpdate) -> Club:
        update_data = schema.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(club, key, value)

        await db.commit()
        await db.refresh(club)
        return club