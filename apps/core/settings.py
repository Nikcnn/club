import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Загружаем переменные из .env файла
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DB
    # Пример: postgresql+asyncpg://user:pass@localhost:5432/db_name
    DATABASE_URL: str 

    # SECURITY
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SUPER_SECRET_STRING_XYZ_123"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Делаем коротким (30 мин)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # Делаем длинным (30 дней)
    # S3 / MinIO (Хранилище файлов)
    S3_ENDPOINT_URL: str | None = None
    S3_PUBLIC_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_BUCKET_PUBLIC: str = "public"
    S3_BUCKET_PRIVATE: str = "private"

    ADMIN_USER_MODEL: str = "User"
    ADMIN_USER_MODEL_USERNAME_FIELD: str = "admin"
    ADMIN_SECRET_KEY: str = "CHANGE_THIS_TO_A_SUPER_SECRET_STRING_XYZ_123"
    # Project Info
    PROJECT_NAME: str = "ClubVerse API"
    API_V1_STR: str = "" # Если нужен префикс /api/v1

    PERSPECTIVE_API_KEY: str | None = None
    MODERATION_ENABLED: bool = True
    MODERATION_PROVIDER: str = "perspective"
    MODERATION_FAIL_MODE: str = "approve"
    TOXICITY_THRESHOLD_PENDING: float = 0.50
    TOXICITY_THRESHOLD_REJECT: float = 0.80

settings = Settings()
