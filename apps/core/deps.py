import logging
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.settings import settings
from apps.db.session import AsyncSessionLocal
from apps.employment.models import TgInfo, CandidateProfile
from apps.organizations.models import Organization
from apps.users.models import User


# 1. Dependency для получения сессии БД
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 2. Настройка схемы авторизации
# tokenUrl указывает Swagger UI, куда отправлять логин/пароль, чтобы получить токен
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


# 3. ГЛАВНАЯ ФУНКЦИЯ ПРОВЕРКИ
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Эта функция вызывается FastAPI каждый раз, когда ендпоинт требует авторизацию.
    Она:
    1. Достает токен из заголовка Authorization: Bearer <token>
    2. Расшифровывает его (jwt.decode)
    3. Проверяет срок действия и подпись
    4. Ищет владельца в базе данных
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")  # Получаем тип

        if user_id is None or token_type != "access":  # <--- ПРОВЕРКА ТИПА
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # ПОИСК В БАЗЕ ДАННЫХ
    # Если токен валиден, проверяем, существует ли такой юзер реально
    query = select(User).where(User.id == int(user_id))
    result = await db.execute(query)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is inactive")

    return user


def _cred_exc():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _get_active_tg_info(db: AsyncSession, tg_user_id: str) -> TgInfo:
    tg = (await db.execute(select(TgInfo).where(TgInfo.telegram_id == tg_user_id))).scalars().first()
    if not tg or not tg.is_active or tg.is_blocked:
        raise _cred_exc()
    return tg


async def _get_linked_entity_by_tg(
    db: AsyncSession,
    tg_user_id: str,
    *,
    linked_id_attr: str,
    model,
):
    tg = await _get_active_tg_info(db, tg_user_id)
    linked_id = getattr(tg, linked_id_attr)
    if not linked_id:
        raise _cred_exc()

    entity = (await db.execute(select(model).where(model.id == linked_id))).scalars().first()
    if not entity or not entity.is_active:
        raise _cred_exc()
    return entity

async def get_current_organization_tg(
    tg_user_id: str = Header(..., alias="X-Tg-User-Id"),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    return await _get_linked_entity_by_tg(
        db,
        tg_user_id,
        linked_id_attr="linked_organization_id",
        model=Organization,
    )

async def get_current_candidate_tg(
    tg_user_id: str = Header(..., alias="X-Tg-User-Id"),
    db: AsyncSession = Depends(get_db),
) -> CandidateProfile:
    return await _get_linked_entity_by_tg(
        db,
        tg_user_id,
        linked_id_attr="linked_candidate_id",
        model=CandidateProfile,
    )
