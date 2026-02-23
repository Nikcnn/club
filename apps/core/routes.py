from fastapi import APIRouter

from apps.core.storage import build_public_url

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/public-url")
async def get_public_media_url(object_key: str):
    """Вернуть публичный URL объекта по его ключу в MinIO/S3."""
    return {"object_key": object_key, "url": build_public_url(object_key)}
