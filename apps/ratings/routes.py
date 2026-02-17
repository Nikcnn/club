from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.ratings.schemas import RatingResponse
from apps.ratings.service import RatingService

router = APIRouter(prefix="/ratings", tags=["Ratings"])

@router.get("/club/{club_id}", response_model=RatingResponse)
async def get_club_rating(
    club_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await RatingService.get_club_rating(db, club_id)

@router.get("/organization/{org_id}", response_model=RatingResponse)
async def get_org_rating(
    org_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await RatingService.get_org_rating(db, org_id)