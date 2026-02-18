from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.investors.schemas import InvestorCreate, InvestorUpdate, InvestorResponse
from apps.investors.services import InvestorService
from apps.users.dependencies import get_current_user
from apps.users.models import User, UserRole
# Чтобы проверить уникальность email
from apps.users.services import UserService

router = APIRouter(prefix="/investors", tags=["Investors"])


# === PUBLIC ===

@router.post("/register", response_model=InvestorResponse, status_code=status.HTTP_201_CREATED)
async def register_investor(
    schema: InvestorCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового инвестора.
    """
    # Проверка на существование email через общий сервис пользователей
    existing_user = await UserService.get_by_email(db, schema.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    return await InvestorService.create(db, schema)


@router.get("/", response_model=List[InvestorResponse])
async def list_investors(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Список инвесторов (например, для администраторов или стартапов).
    """
    return await InvestorService.get_all(db, skip, limit)


@router.get("/{investor_id}", response_model=InvestorResponse)
async def get_investor_profile(
    investor_id: int,
    db: AsyncSession = Depends(get_db)
):
    investor = await InvestorService.get_by_id(db, investor_id)
    if not investor:
        raise HTTPException(status_code=404, detail="Инвестор не найден")
    return investor


# === PROTECTED ===

@router.patch("/me", response_model=InvestorResponse)
async def update_my_profile(
    schema: InvestorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновление своего профиля инвестора.
    """
    if current_user.role != UserRole.INVESTOR:
        raise HTTPException(status_code=403, detail="Только инвесторы могут редактировать этот профиль")

    # Загружаем модель Investor (current_user может быть загружен как User)
    investor = await InvestorService.get_by_id(db, current_user.id)

    return await InvestorService.update(db, investor, schema)
