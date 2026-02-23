from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, HttpUrl


class InvestorBase(BaseModel):
    bio: Optional[str] = None
    company_name: Optional[str] = Field(None, max_length=150)
    linkedin_url: Optional[str] = None  # Можно использовать HttpUrl, но str проще для начала
    avatar_key: Optional[str] = None


class InvestorCreate(InvestorBase):
    email: EmailStr
    username: None = None
    password: str = Field(..., min_length=6)


class InvestorUpdate(BaseModel):
    bio: Optional[str] = None
    company_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_key: Optional[str] = None


class InvestorResponse(InvestorBase):
    id: int
    email: EmailStr
    role: str  # UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)