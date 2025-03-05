"""
MinIO client – reads raw documents from the object store.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import io
import os

from minio import Minio

_MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
_MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
_MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
_MINIO_BUCKET = os.getenv("MINIO_RAW_BUCKET", "chatopsllm-raw")
_MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


def _get_client() -> Minio:
    return Minio(
        _MINIO_ENDPOINT,
        access_key=_MINIO_ACCESS_KEY,
        secret_key=_MINIO_SECRET_KEY,
        secure=_MINIO_SECURE,
    )


def list_raw_objects(prefix: str = "") -> list[str]:
    """Return all object keys in the raw bucket, optionally filtered by *prefix*."""
    client = _get_client()
    objects = client.list_objects(_MINIO_BUCKET, prefix=prefix, recursive=True)
    return [obj.object_name for obj in objects]


def read_object(object_key: str) -> str:
    """Download *object_key* from MinIO and return its text content."""
    client = _get_client()
    response = client.get_object(_MINIO_BUCKET, object_key)
    try:
        return response.read().decode("utf-8")
    finally:
        response.close()
        response.release_conn()
