from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from apps.users.models import UserRole


class UserCreateBase(BaseModel):
    email: EmailStr
    password: str
    avatar_key: Optional[str] = None


class UserResponseBase(BaseModel):
    id: int
    email: EmailStr
    avatar_key: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
