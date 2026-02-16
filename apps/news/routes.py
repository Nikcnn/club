from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.users.models import User, UserRole

from apps.news.schemas import NewsCreate, NewsResponse, NewsUpdate
from apps.news.services import NewsService

router = APIRouter(prefix="/news", tags=["News"])


# === PUBLIC ===

@router.get("/", response_model=List[NewsResponse])
async def list_news(
    club_id: Optional[int] = Query(None, description="Фильтр новостей по конкретному клубу"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить ленту новостей (общую или конкретного клуба).
    """
    return await NewsService.get_all(db, club_id, skip, limit)


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news_detail(
    news_id: int,
    db: AsyncSession = Depends(get_db)
):
    news = await NewsService.get_by_id(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="Новость не найдена")
    return news


# === PROTECTED (CLUBS ONLY) ===

@router.post("/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(
    schema: NewsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.CLUB:
        raise HTTPException(status_code=403, detail="Только клубы могут публиковать новости")

    return await NewsService.create(db, schema, club_id=current_user.id)


@router.patch("/{news_id}", response_model=NewsResponse)
async def update_news(
    news_id: int,
    schema: NewsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Редактировать новость. Доступно только автору (клубу).
    """
    news = await NewsService.get_by_id(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="Новость не найдена")

    # Проверка прав: редактировать может только создатель
    if news.club_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не являетесь автором этой новости")

    return await NewsService.update(db, news_id, schema)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(
    news_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить новость.
    """
    news = await NewsService.get_by_id(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="Новость не найдена")

    if news.club_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не можете удалить чужую новость")

    await NewsService.delete(db, news_id)
    return None