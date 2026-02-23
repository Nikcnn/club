import pytest
from fastapi import HTTPException

from apps.core import storage


def test_parse_minio_endpoint_with_https_url() -> None:
    endpoint, secure = storage._parse_minio_endpoint("https://s3.example.com")

    assert endpoint == "s3.example.com"
    assert secure is True


def test_parse_minio_endpoint_without_scheme() -> None:
    endpoint, secure = storage._parse_minio_endpoint("minio:9000")

    assert endpoint == "minio:9000"
    assert secure is False


def test_parse_minio_endpoint_empty_raises() -> None:
    with pytest.raises(HTTPException) as exc:
        storage._parse_minio_endpoint("")

    assert exc.value.status_code == 500


def test_build_public_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage.settings, "S3_PUBLIC_ENDPOINT_URL", "https://cdn.example.com")
    monkeypatch.setattr(storage.settings, "S3_ENDPOINT_URL", None)
    monkeypatch.setattr(storage.settings, "S3_BUCKET_PUBLIC", "public")

    url = storage.build_public_url("users/1/avatar.png")

    assert url == "https://cdn.example.com/public/users/1/avatar.png"
