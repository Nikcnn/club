from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.db.dependencies import get_db
from apps.users.dependencies import get_current_user
from apps.users.models import User, UserRole

# Импорт обновленных схем и сервисов
from apps.funding.schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    InvestmentCreate,
    InvestmentResponse
)
from apps.funding.services import CampaignService, InvestmentService

router = APIRouter(prefix="/funding", tags=["Funding"])

# ==========================================
# 1. CAMPAIGNS
# ==========================================

@router.get("/campaigns/", response_model=List[CampaignResponse])
async def list_campaigns(
    club_id: Optional[int] = Query(None, description="ID клуба"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await CampaignService.get_all(db, club_id=club_id, skip=skip, limit=limit)

@router.post("/campaigns/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    schema: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.CLUB:
        raise HTTPException(status_code=403, detail="Только клубы могут создавать сборы.")

    # Создаем кампанию, привязывая к ID пользователя (клуба)
    return await CampaignService.create(db, schema, club_id=current_user.id)

@router.get("/campaigns/{campaign_id}/", response_model=CampaignResponse)
async def get_campaign_detail(
    campaign_id: int,
    db: AsyncSession = Depends(get_db)
):
    campaign = await CampaignService.get_by_id(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Кампания не найдена.")
    return campaign

@router.patch("/campaigns/{campaign_id}/", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    schema: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить кампанию. Проверяем, что текущий юзер — владелец клуба.
    """
    campaign = await CampaignService.get_by_id(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Кампания не найдена.")

    # Проверка прав: редактировать может только создатель (клуб)
    if campaign.club_id != current_user.id:
         raise HTTPException(status_code=403, detail="Вы не являетесь владельцем этой кампании.")

    updated_campaign = await CampaignService.update(db, campaign_id, schema)
    return updated_campaign

# ==========================================
# 2. INVESTMENTS
# ==========================================

@router.post("/investments/", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
async def create_investment(
    schema: InvestmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверяем, существует ли кампания
    campaign = await CampaignService.get_by_id(db, schema.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Целевая кампания не найдена.")

    return await InvestmentService.create(db, schema, user_id=current_user.id)

@router.get("/investments/my/", response_model=List[InvestmentResponse])
async def get_my_investments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await InvestmentService.get_by_user(db, user_id=current_user.id)

@router.get("/investments/{investment_id}/", response_model=InvestmentResponse)
async def get_investment_detail(
    investment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    investment = await InvestmentService.get_by_id(db, investment_id)
    if not investment:
        raise HTTPException(status_code=404, detail="Инвестиция не найдена.")

    # Доступ только для владельца инвестиции или администратора
    if investment.investor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен.")

    return investment