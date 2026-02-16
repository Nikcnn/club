from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, HttpUrl


# === BASE ===
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    city: str
    description: Optional[str] = None
    website: Optional[str] = None
    logo_key: Optional[str] = None


# === CREATE ===
class OrganizationCreate(OrganizationBase):
    email: EmailStr
    password: str = Field(..., min_length=6)


# === UPDATE ===
class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    logo_key: Optional[str] = None


# === RESPONSE ===
class OrganizationResponse(OrganizationBase):
    id: int
    email: EmailStr
    role: str  # UserRole
    is_active: bool

    # Для рейтинга (если нужно выводить сразу)
    # rating: Optional[RatingResponse] = None

    model_config = ConfigDict(from_attributes=True)