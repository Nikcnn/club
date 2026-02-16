from pydantic import BaseModel, condecimal
from datetime import datetime
from typing import Optional


# Базовая схема
class CampaignBase(BaseModel):
    title: str
    description: str
    goal_amount: condecimal(gt=0, decimal_places=2)  # type: ignore
    ends_at: datetime
    currency: str = "KZT"


class CampaignCreate(CampaignBase):
    pass  # club_id возьмем из текущего юзера


class CampaignResponse(CampaignBase):
    id: int
    club_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Схема для инвестиции
class InvestmentCreate(BaseModel):
    amount: condecimal(gt=0, decimal_places=2)  # type: ignore
    currency: str = "KZT"