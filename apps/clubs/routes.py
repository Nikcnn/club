from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.users.models import User, UserRole
from apps.clubs.schemas import ClubCreate, ClubUpdate, ClubResponse
from apps.clubs.services import ClubService
from apps.clubs.models import Club

router = APIRouter(prefix="/clubs", tags=["Clubs"])

# TODO(search): при добавлении delete-эндпоинта клуба вызывать SearchService.delete_point("club", club_id) после commit.


# === PUBLIC ENDPOINTS ===

@router.post("/register", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
async def register_club(
    schema: ClubCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового клуба.
    """
    # Тут хорошо бы добавить проверку на существование email через UserService
    return await ClubService.create(db, schema)


@router.get("/", response_model=List[ClubResponse])
async def list_clubs(
    city: Optional[str] = Query(None, description="Фильтр по городу"),
    category: Optional[str] = Query(None, description="Фильтр по категории (IT, Sport...)"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Каталог клубов с фильтрацией (The Hub).
    """
    return await ClubService.get_all(db, city, category, search, skip, limit)


@router.get("/{club_id}", response_model=ClubResponse)
async def get_club_profile(
    club_id: int,
    db: AsyncSession = Depends(get_db)
):
    club = await ClubService.get_by_id(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


# === PROTECTED ENDPOINTS ===

@router.patch("/me", response_model=ClubResponse)
async def update_my_club_profile(
    schema: ClubUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновление профиля. Доступно только авторизованному Клубу.
    """
    if current_user.role != UserRole.CLUB:
        raise HTTPException(status_code=403, detail="Only clubs can edit club profiles")

    # Получаем именно модель Club (так как current_user это модель User)
    # Благодаря полиморфизму, если мы загрузили User и это Клуб, SQLAlchemy подтянет данные,
    # но для чистоты типов лучше запросить через сервис.
    club = await ClubService.get_by_id(db, current_user.id)

    return await ClubService.update(db, club, schema)
