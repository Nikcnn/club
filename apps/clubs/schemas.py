from typing import Optional, Dict
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Базовые схемы User (предполагаем, что они есть в apps/users/schemas.py)
# Если нет, можно просто использовать поля email/password напрямую здесь.

class ClubBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., description="Категория: IT, Sport, Art и т.д.")
    city: str
    description: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[Dict[str, str]] = Field(default_factory=dict)
    edu_org_id: Optional[int] = None


class ClubCreate(ClubBase):
    email: EmailStr
    password: str = Field(..., min_length=6)

class ClubUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    logo_key: Optional[str] = None
    edu_org_id: Optional[int] = None


class ClubResponse(ClubBase):
    id: int
    email: EmailStr
    logo_key: Optional[str] = None

    # Настройка для ORM (Pydantic v2)
    model_config = ConfigDict(from_attributes=True)
