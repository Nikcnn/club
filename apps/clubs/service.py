from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.clubs.models import Club
from apps.clubs.schemas import ClubCreate
from apps.users.models import UserRole


class ClubService:
    @staticmethod
    async def create(db: AsyncSession, schema: ClubCreate) -> Club:
        # hash = get_password_hash...
        hash = "secret"

        club = Club(
            email=schema.email,
            hashed_password=hash,
            role=UserRole.CLUB,
            name=schema.name,
            category=schema.category,
            city=schema.city,
            description=schema.description
        )

        db.add(club)
        await db.commit()  # <--- Добавился await
        await db.refresh(club)  # <--- Добавился await
        return club

    @staticmethod
    async def get_by_id(db: AsyncSession, club_id: int) -> Club | None:
        # Старый стиль: db.query(Club).filter(...).first() - НЕ РАБОТАЕТ В ASYNC

        # Новый стиль:
        query = select(Club).where(Club.id == club_id)
        result = await db.execute(query)  # <--- Выполняем асинхронно
        return result.scalars().first()