from __future__ import annotations

from typing import Optional, Tuple
from urllib.parse import urlparse
from minio import Minio
from app.config import load_settings


_client: Optional[Minio] = None


def _build_client() -> Minio:
    settings = load_settings()
    if not settings.Minio:
        raise RuntimeError("Minio config missing")

    endpoint = settings.Minio.endpoint
    secure = False
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        parsed = urlparse(endpoint)
        endpoint = parsed.netloc
        secure = parsed.scheme == "https"

    return Minio(
        endpoint,
        access_key=settings.Minio.accessKey,
        secret_key=settings.Minio.secretKey,
        secure=secure,
        region=settings.Minio.region,
    )


def get_client() -> Minio:
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def ensure_bucket(bucket: str) -> None:
    client = get_client()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def upload_file(local_path: str, key: str, content_type: Optional[str] = None) -> str:
    settings = load_settings()
    if not settings.Minio:
        raise RuntimeError("Minio config missing")

    bucket = settings.Minio.bucket
    ensure_bucket(bucket)

    client = get_client()
    client.fput_object(bucket, key, local_path, content_type=content_type)
    return key


def get_object_stream(key: str) -> Tuple[object, Optional[str], Optional[int]]:
    settings = load_settings()
    if not settings.Minio:
        raise RuntimeError("Minio config missing")

    client = get_client()
    bucket = settings.Minio.bucket
    stat = client.stat_object(bucket, key)
    obj = client.get_object(bucket, key)
    return obj, stat.content_type, stat.size
