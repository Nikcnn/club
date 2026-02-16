from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CompetitionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    starts_at: datetime
    ends_at: datetime


class CompetitionResponse(CompetitionCreate):
    id: int
    club_id: int
    status: str

    class Config:
        from_attributes = True