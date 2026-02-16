# apps/users/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# Базовая схема для создания (пароль + email)
class UserCreateBase(BaseModel):
    email: EmailStr
    password: str
    # Общие поля для всех (если есть в модели User)
    avatar_key: Optional[str] = None


# Базовая схема для ответа (без пароля)
class UserResponseBase(BaseModel):
    id: int
    email: EmailStr
    avatar_key: Optional[str] = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True  # Для совместимости с SQLAlchemy