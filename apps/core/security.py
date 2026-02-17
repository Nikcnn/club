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
def create_access_token(subject: Union[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Создание JWT токена.
    subject: Обычно это ID пользователя (как строка).
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Payload токена
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt