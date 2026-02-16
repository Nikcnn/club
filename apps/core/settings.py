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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней

    # S3 / MinIO (Хранилище файлов)
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_BUCKET_PUBLIC: str = "public"
    S3_BUCKET_PRIVATE: str = "private"

    # Project Info
    PROJECT_NAME: str = "ClubVerse API"
    API_V1_STR: str = "" # Если нужен префикс /api/v1

settings = Settings()