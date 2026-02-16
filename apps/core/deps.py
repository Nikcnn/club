from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from apps.db.session import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Заглушка под текущего пользователя
# (в реальном проекте будет JWT/Session/fastapi-users и т.д.)
class CurrentUser:
    def __init__(self, id: int, is_admin: bool = False):
        self.id = id
        self.is_admin = is_admin

async def get_current_user() -> CurrentUser:
    return CurrentUser(id=1, is_admin=True)
