from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.reviews.schemas import ReviewCreate, ReviewResponse
from apps.reviews.services import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/club/{club_id}", response_model=ReviewResponse)
async def review_club(
    club_id: int,
    schema: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await ReviewService.add_club_review(db, schema, current_user.id, club_id)

@router.post("/organization/{org_id}", response_model=ReviewResponse)
async def review_organization(
    org_id: int,
    schema: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await ReviewService.add_org_review(db, schema, current_user.id, org_id)