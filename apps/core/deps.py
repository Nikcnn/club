from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.settings import settings
from apps.core.security import ALGORITHM  # или settings.ALGORITHM
from apps.db.session import AsyncSessionLocal
from apps.users.models import User


# === 1. Dependency для БД ===
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Создает сессию базы данных для каждого запроса.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# === 2. Dependency для Авторизации ===

# Указываем URL, по которому фронтенд может получить токен (для Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Валидация токена и получение текущего пользователя из БД.
    Используется во всех защищенных ручках: current_user: User = Depends(get_current_user)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Декодируем токен
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        # P.S. Тут можно также проверять role из токена, если она там есть

    except JWTError:
        raise credentials_exception

    # Ищем пользователя в БД
    # Используем select(User), чтобы найти и Admin, и Club, и Investor (полиморфизм)
    query = select(User).where(User.id == int(user_id))
    result = await db.execute(query)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is inactive")

    return user