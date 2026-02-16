from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user  # Предполагаем наличие
from apps.campaigns.schemas import CampaignCreate, CampaignResponse, InvestmentCreate
from apps.campaigns.services import CampaignService
from apps.users.models import User, UserRole

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("/", response_model=CampaignResponse)
def create_campaign(
    schema: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.CLUB:
        raise HTTPException(403, "Only clubs can create campaigns")

    return CampaignService.create_campaign(db, schema, club_id=current_user.id)


@router.post("/{campaign_id}/invest")
def invest_in_campaign(
    campaign_id: int,
    schema: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Инвестировать может кто угодно (или только инвесторы - решайте сами)
    return CampaignService.create_investment(db, schema, campaign_id, current_user.id)