from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user  # Зависимость для получения текущего юзера
from apps.users.models import User
from apps.users.schemas import UserCreateBase, UserResponseBase, Token
from apps.users.services import UserService
from apps.core.config import settings  # Предполагаем наличие настроек
from apps.core.security import create_access_token  # Функция генерации JWT

router = APIRouter(prefix="/users", tags=["Users & Auth"])


@router.post("/register", response_model=UserResponseBase, status_code=status.HTTP_201_CREATED)
async def register_member(
    schema: UserCreateBase,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация обычного пользователя (UserRole.MEMBER).
    """
    existing_user = await UserService.get_by_email(db, schema.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже существует"
        )

    return await UserService.create_member(db, schema)


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение JWT токена (Login).
    OAuth2PasswordRequestForm требует поля username (здесь email) и password.
    """
    user = await UserService.authenticate(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь не активен")

    # Генерация токена
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponseBase)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Получить профиль текущего авторизованного пользователя.
    """
    return current_user