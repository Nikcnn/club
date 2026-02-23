from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.investors.models import Investor
from apps.users.models import UserRole
from apps.investors.schemas import InvestorCreate, InvestorUpdate
from apps.users.utils import get_password_hash  # Функция из apps/users/utils.py


class InvestorService:
    @staticmethod
    async def create(db: AsyncSession, schema: InvestorCreate) -> Investor:
        # 1. Хешируем пароль
        hashed_pw = get_password_hash(schema.password)

        # 2. Создаем инвестора
        investor = Investor(
            email=schema.email,
            hashed_password=hashed_pw,  # Поле из User
            role=UserRole.INVESTOR,  # Принудительно ставим роль
            is_active=True,
            username=schema.email,
            # Поля Investor
            bio=schema.bio,
            company_name=schema.company_name,
            linkedin_url=schema.linkedin_url,
            avatar_key=schema.avatar_key
        )

        db.add(investor)
        await db.commit()
        await db.refresh(investor)
        return investor

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[Investor]:
        query = select(Investor).where(Investor.id == user_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20
    ) -> List[Investor]:
        query = select(Investor).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(
        db: AsyncSession,
        investor: Investor,
        schema: InvestorUpdate
    ) -> Investor:
        update_data = schema.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(investor, key, value)

        await db.commit()
        await db.refresh(investor)
        return investor