from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.reviews.schemas import ModerationHealthResponse, ReviewCreate, ReviewResponse
from apps.reviews.services import ReviewService
from apps.moderation.service import ModerationService
from apps.users.dependencies import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/club/{club_id}", response_model=ReviewResponse)
async def review_club(
    club_id: int,
    schema: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await ReviewService.add_club_review(db, schema, current_user.id, club_id)


@router.post("/organization/{org_id}", response_model=ReviewResponse)
async def review_organization(
    org_id: int,
    schema: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await ReviewService.add_org_review(db, schema, current_user.id, org_id)


@router.get("/club/{club_id}", response_model=list[ReviewResponse])
async def list_club_reviews(
    club_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await ReviewService.list_club_reviews(db, club_id)


@router.get("/organization/{org_id}", response_model=list[ReviewResponse])
async def list_org_reviews(
    org_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await ReviewService.list_org_reviews(db, org_id)


@router.get("/moderation/health", response_model=ModerationHealthResponse)
async def moderation_health(
    current_user=Depends(get_current_user),
):
    _ = current_user
    return await ModerationService.provider_healthcheck()
