from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.security import get_password_hash, verify_password
from apps.news.models import News
from apps.users.models import User, UserRole
from apps.users.schemas import UserCreateBase


class UserService:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def create_member(db: AsyncSession, schema: UserCreateBase) -> User:
        user = User(
            email=schema.email,
            hashed_password=get_password_hash(schema.password),
            username=schema.username,
            role=UserRole.MEMBER,
            avatar_key=schema.avatar_key,
            is_active=True,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
        user = await UserService.get_by_email(db, email)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user


