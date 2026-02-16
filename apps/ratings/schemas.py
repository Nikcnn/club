from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class RatingResponse(BaseModel):
    avg_score: Decimal = Field(..., description="Средний рейтинг (например, 4.50)")
    review_count: int = Field(..., description="Количество отзывов")

    model_config = ConfigDict(from_attributes=True)
