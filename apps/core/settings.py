from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str  # DATABASE_URL=postgresql+asyncpg://postgres:pass@localhost:5432/club_db

    # S3 / MinIO
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_BUCKET_PUBLIC: str | None = None
    S3_BUCKET_PRIVATE: str | None = None

    SECRET_KEY: str = "CHANGE_THIS_TO_A_SUPER_SECRET_STRING_XYZ_123" # Сгенерируйте сложный ключ!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней
settings = Settings()
