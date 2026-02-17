from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

# Импортируем Enums из моделей, чтобы не дублировать логику
# (Предполагается, что они доступны в models.py, иначе можно определить здесь)
from apps.funding.models import CampaignStatus, InvestmentStatus, FundingType

# =======================
# CAMPAIGNS
# =======================

class CampaignBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str
    goal_amount: Decimal = Field(..., gt=0, max_digits=14, decimal_places=2)
    starts_at: datetime
    ends_at: datetime
    cover_key: Optional[str] = None
    gallery_keys: List[str] = Field(default_factory=list)

    @field_validator("ends_at")
    @classmethod
    def validate_dates(cls, v, info):
        # Проверяем, есть ли starts_at в переданных данных
        start = info.data.get("starts_at")
        if start and v <= start:
            raise ValueError("Дата окончания должна быть позже даты начала")
        return v
class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    goal_amount: Optional[Decimal] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    status: Optional[CampaignStatus] = None
    cover_key: Optional[str] = None
    gallery_keys: Optional[List[str]] = None

class CampaignResponse(CampaignBase):
    id: int
    club_id: int
    status: CampaignStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Поле для отображения собранной суммы (вычисляется отдельно)
    current_amount: Decimal = Field(default=0.0)

    model_config = ConfigDict(from_attributes=True)


# =======================
# INVESTMENTS
# =======================

class InvestmentCreate(BaseModel):
    campaign_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    type: FundingType = FundingType.DONATION

class InvestmentResponse(BaseModel):
    id: int
    campaign_id: int
    investor_id: int
    amount: Decimal
    status: InvestmentStatus
    type: FundingType
    created_at: datetime
    paid_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)