from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.users.models import User, UserRole
from apps.users.schemas import UserCreateBase
from apps.users.utils import get_password_hash, verify_password


class UserService:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        # select(User) вернет и Club, и Organization благодаря полиморфизму
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def create_member(db: AsyncSession, schema: UserCreateBase) -> User:
        """
        Создание обычного пользователя (MEMBER).
        Клубы и Организации создаются через свои сервисы, но используют ту же таблицу.
        """
        hashed_pw = get_password_hash(schema.password)

        user = User(
            email=schema.email,
            hashed_password=hashed_pw,
            role=UserRole.MEMBER,  # Явно задаем роль
            avatar_key=schema.avatar_key,
            is_active=True
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Проверка логина и пароля. Возвращает User или None.
        """
        user = await UserService.get_by_email(db, email)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user