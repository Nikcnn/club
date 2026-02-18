import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from apps.core.settings import settings

security = HTTPBasic()


def admin_basic_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    is_valid_username = secrets.compare_digest(credentials.username, settings.ADMIN_USERNAME)
    is_valid_password = secrets.compare_digest(credentials.password, settings.ADMIN_PASSWORD)

    if not (is_valid_username and is_valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
