from datetime import datetime  # <--- Обязательный импорт
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    text: str
    score: int = Field(..., ge=1, le=5)  # Оценка от 1 до 5


class ReviewResponse(ReviewCreate):
    id: int
    user_id: int
    created_at: datetime  # или datetime

    class Config:
        from_attributes = True