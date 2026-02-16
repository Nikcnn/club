from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NewsCreate(BaseModel):
    title: str
    body: str
    is_published: bool = True


class NewsResponse(NewsCreate):
    id: int
    club_id: int
    created_at: datetime

    class Config:
        from_attributes = True