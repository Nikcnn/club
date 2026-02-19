from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SearchSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "clubverse_search"

    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_SIZE: int | None = None

    SEARCH_SCORE_THRESHOLD: float | None = None


    @field_validator("SEARCH_SCORE_THRESHOLD", mode="before")
    @classmethod
    def normalize_search_score_threshold(cls, value: object) -> object:
        """Handle malformed env values like `0.3    ADMIN_USERNAME=...`."""

        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            return cleaned.split()[0]
        return value

    PERSONALIZATION_ENABLED: bool = True
    ROLE_BOOST_WEIGHT: float = 0.05
    PREF_CITY_WEIGHT: float = 0.02
    PREF_CATEGORY_WEIGHT: float = 0.02
    PREF_TYPE_WEIGHT: float = 0.02


@lru_cache(maxsize=1)
def get_search_settings() -> SearchSettings:
    return SearchSettings()
