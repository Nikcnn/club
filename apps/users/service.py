from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional
from apps.users.models import UserRole

# === Базовые схемы (уже были) ===
class UserCreateBase(BaseModel):
    email: EmailStr
    password: str
    avatar_key: Optional[str] = None

class UserResponseBase(BaseModel):
    id: int
    email: EmailStr
    avatar_key: Optional[str] = None
    role: UserRole # Используем Enum
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# === Новые схемы для Auth ===

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None