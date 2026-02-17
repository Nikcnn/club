from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.security import create_access_token, create_refresh_token  # Функция генерации JWT
from apps.core.settings import settings
from apps.core.storage import upload_image_to_minio
from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.users.models import User
from apps.users.schemas import UserCreateBase, UserResponseBase, Token, TokenRefreshRequest
from apps.users.services import UserService
from jose import jwt, JWTError

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


# === LOGIN ===
@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await UserService.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Генерируем ПАРУ токенов
    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


# === REFRESH ===
@router.post("/refresh", response_model=Token)  # Обратите внимание: response_model=Token (а не TokenRefreshRequest)
async def refresh_token(
    request_data: TokenRefreshRequest,  # <--- Вот так принимаем JSON в теле
    db: AsyncSession = Depends(get_db)
):
    # Достаем токен из модели
    refresh_token = request_data.refresh_token

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Декодируем Refresh Token
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "refresh":
            raise credentials_exception

        user = await UserService.get_by_id(db, int(user_id))
        if not user or not user.is_active:
            raise credentials_exception

        new_access_token = create_access_token(subject=user.id)

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except JWTError:
        raise credentials_exception


@router.get("/me", response_model=UserResponseBase)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Получить профиль текущего авторизованного пользователя.
    """
    return current_user


@router.post("/me/avatar", response_model=UserResponseBase)
async def upload_my_avatar(
    avatar: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Загрузить аватар текущего пользователя в MinIO.
    - Файл кладется в публичный бакет в папку users/{user_id}/
    - В БД сохраняется avatar_key (ключ объекта в бакете)
    Возвращает обновленного пользователя.
    """
    object_key = await upload_image_to_minio(avatar, folder=f"users/{current_user.id}")
    current_user.avatar_key = object_key
    await db.commit()
    await db.refresh(current_user)
    return current_user
