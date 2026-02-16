from typing import Optional
from apps.users.schemas import UserCreateBase, UserResponseBase

class InvestorCreate(UserCreateBase):
    bio: Optional[str] = None
    # Другие специфичные поля инвестора, если есть

class InvestorResponse(UserResponseBase):
    bio: Optional[str]