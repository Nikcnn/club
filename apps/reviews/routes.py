from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.users.models import User
from apps.reviews.schemas import ReviewCreate, ReviewResponse
from apps.reviews.services import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])

# ==========================
# CLUB ROUTES
# ==========================

@router.get("/club/{club_id}", response_model=List[ReviewResponse])
async def get_club_reviews(
    club_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список отзывов о клубе.
    """
    return await ReviewService.get_club_reviews(db, club_id, skip, limit)

@router.post("/club/{club_id}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_club_review(
    club_id: int,
    schema: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Оставить отзыв клубу (только авторизованные пользователи).
    """
    try:
        # Можно добавить проверку: нельзя оставлять отзыв своему же клубу
        if current_user.id == club_id:
             raise HTTPException(status_code=400, detail="Нельзя оценивать собственный клуб.")

        return await ReviewService.add_club_review(db, schema, current_user.id, club_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================
# ORGANIZATION ROUTES
# ==========================

@router.get("/organization/{org_id}", response_model=List[ReviewResponse])
async def get_org_reviews(
    org_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    return await ReviewService.get_org_reviews(db, org_id, skip, limit)

@router.post("/organization/{org_id}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_org_review(
    org_id: int,
    schema: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await ReviewService.add_org_review(db, schema, current_user.id, org_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))