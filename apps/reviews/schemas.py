from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    text: str
    score: int = Field(..., ge=1, le=5)


class ReviewResponse(ReviewCreate):
    id: int
    user_id: int
    created_at: datetime
    is_approved: bool
    moderation_status: str
    toxicity_score: float | None = None

    class Config:
        from_attributes = True
