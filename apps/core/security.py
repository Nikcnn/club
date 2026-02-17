from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt

from apps.core.settings import settings

# Настройка хеширования паролей (bcrypt)

from pwdlib import PasswordHash

# Использует рекомендуемый алгоритм (обычно Argon2, если установлен)
password_hash = PasswordHash.recommended()

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from apps.core.settings import settings

# ... (verify_password и get_password_hash оставляем как были) ...

def create_access_token(subject: Union[str, Any]) -> str:
    """Создает короткоживущий токен доступа."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access" # ВАЖНО: пометка типа
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Union[str, Any]) -> str:
    """Создает долгоживущий токен обновления."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh" # ВАЖНО: пометка типа
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)