from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Мини-схема для отображения автора отзыва
class ReviewAuthor(BaseModel):
    id: int
    email: str
    avatar_key: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    text: Optional[str] = None
    score: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5")


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    author: Optional[ReviewAuthor] = None  # Подгруженный автор
    text: Optional[str]
    score: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)