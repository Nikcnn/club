import uuid
from io import BytesIO
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile

from apps.core.settings import settings

import logging



logger = logging.getLogger("uvicorn.error")
def _parse_minio_endpoint(endpoint_url: str | None) -> tuple[str, bool]:
    endpoint = (endpoint_url or "").strip()
    if not endpoint:
        raise HTTPException(status_code=500, detail="S3_ENDPOINT_URL is not configured")

    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        parsed = urlparse(endpoint)
        if not parsed.netloc:
            raise HTTPException(status_code=500, detail="S3_ENDPOINT_URL is invalid")
        return parsed.netloc, parsed.scheme == "https"
    logger.info(endpoint.rstrip("/"))
    return endpoint.rstrip("/"), False


def _build_public_object_url(bucket: str, object_name: str) -> str:
    endpoint = (settings.S3_PUBLIC_ENDPOINT_URL or settings.S3_ENDPOINT_URL or "").rstrip("/")
    if not endpoint:
        raise HTTPException(status_code=500, detail="S3 public endpoint is not configured")

    if not endpoint.startswith(("http://", "https://")):
        endpoint = f"http://{endpoint}"
    logger.info(f"{endpoint}/{bucket}/{object_name}")
    return f"{endpoint}/{bucket}/{object_name}"


async def upload_image_to_minio(file: UploadFile, folder: str) -> str:
    """
    Загружает изображение в MinIO (S3-совместимое хранилище) в публичный бакет
    и возвращает КЛЮЧ объекта (object_key), а не URL.
    Пример возвращаемого значения: "users/42/0f1a2b3c4d.png".
    Чтобы получить публичный URL, используйте build_public_url(object_key).
    """
    if not settings.S3_ACCESS_KEY or not settings.S3_SECRET_KEY:
        raise HTTPException(status_code=500, detail="MinIO credentials are not configured")

    try:
        from minio import Minio
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="minio package is not installed") from exc

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "bin"
    object_name = f"{folder}/{uuid.uuid4().hex}.{ext}"

    minio_endpoint, secure = _parse_minio_endpoint(settings.S3_ENDPOINT_URL)

    client = Minio(
        minio_endpoint,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        secure=secure,
    )

    bucket = settings.S3_BUCKET_PUBLIC
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    client.put_object(
        bucket,
        object_name,
        BytesIO(raw),
        length=len(raw),
        content_type=file.content_type,
    )
    logger.info(object_name)
    return object_name


async def upload_image_to_s3(file: UploadFile, folder: str) -> str:
    """Публичный алиас с корректным именем для S3-хранилища."""
    return await upload_image_to_minio(file=file, folder=folder)


def build_public_url(object_name: str) -> str:
    """Собирает публичный URL объекта по ключу."""
    return _build_public_object_url(settings.S3_BUCKET_PUBLIC, object_name)
