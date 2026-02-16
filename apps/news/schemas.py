from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class NewsBase(BaseModel):
    title: str = Field(..., max_length=200)
    body: str
    cover_key: Optional[str] = None
    is_published: bool = True

class NewsCreate(NewsBase):
    pass

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    cover_key: Optional[str] = None
    is_published: Optional[bool] = None

class NewsResponse(NewsBase):
    id: int
    club_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)