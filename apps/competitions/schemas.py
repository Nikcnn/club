from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from apps.competitions.models import CompetitionStatus

class CompetitionBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    starts_at: datetime
    ends_at: datetime

    @field_validator("ends_at")
    @classmethod
    def validate_dates(cls, v, info):
        if "starts_at" in info.data and v <= info.data["starts_at"]:
            raise ValueError("Дата окончания должна быть позже даты начала")
        return v

class CompetitionCreate(CompetitionBase):
    pass

class CompetitionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    status: Optional[CompetitionStatus] = None

class CompetitionResponse(CompetitionBase):
    id: int
    club_id: int
    status: CompetitionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)