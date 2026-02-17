import uuid
from io import BytesIO

from fastapi import HTTPException, UploadFile

from apps.core.settings import settings


def build_public_url(object_key: str, bucket: str | None = None) -> str:
    """
    Построить публичный URL для объекта в бакете по его ключу.
    Возвращает endpoint/bucket/object_key.
    """
    endpoint = (settings.S3_ENDPOINT_URL or "").rstrip("/")
    if not endpoint:
        raise HTTPException(status_code=500, detail="S3_ENDPOINT_URL is not configured")
    _bucket = bucket or settings.S3_BUCKET_PUBLIC
    return f"{endpoint}/{_bucket}/{object_key}"


async def upload_image_to_minio(file: UploadFile, folder: str) -> str:
    """
    Загружает изображение в MinIO в публичный бакет и возвращает КЛЮЧ объекта (object_key), а не URL.
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

    ext = (file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "bin")
    object_name = f"{folder}/{uuid.uuid4().hex}.{ext}"

    endpoint = settings.S3_ENDPOINT_URL or ""
    endpoint = endpoint.replace("http://", "").replace("https://", "")

    client = Minio(
        endpoint,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        secure=(settings.S3_ENDPOINT_URL or "").startswith("https://"),
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

    # Возвращаем ключ (для хранения в *_key колонках)
    return object_name
