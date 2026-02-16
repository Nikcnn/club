from pydantic import BaseModel
from apps.users.schemas import UserCreateBase, UserResponseBase

# 1. Входные данные (Регистрация клуба)
class ClubCreate(UserCreateBase):
    name: str           # Название клуба
    category: str
    city: str
    description: str | None = None

# 2. Выходные данные (Ответ API)
class ClubResponse(UserResponseBase):
    name: str
    category: str
    city: str
    description: str | None
    # organization_id: int | None # Если нужно отдавать ID организации