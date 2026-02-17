from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from apps.core.settings import settings


class AdminAuthBackend(AuthenticationBackend):
    """Простая форма логина для админ-панели."""

    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)
        self._username = settings.ADMIN_USERNAME
        self._password = settings.ADMIN_PASSWORD

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if username == self._username and password == self._password:
            request.session.update({"admin_token": "ok"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin_token") == "ok"
