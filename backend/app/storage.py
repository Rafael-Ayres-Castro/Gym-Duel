"""Private photo storage behind one small interface, with short-lived signed read URLs.

- LocalStorage: files on disk outside the public folder (development). Read URLs point to
  /api/photos/... and carry an HMAC signature with an expiry.
- S3Storage: any S3-compatible bucket (AWS S3, Cloudflare R2, Supabase Storage) kept private;
  read URLs are the provider's presigned URLs.

Only the two members ever receive these URLs, because they are handed out by authenticated
endpoints; the signature and the short expiry keep a leaked link from working for long.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from pathlib import Path
from typing import Protocol
from urllib.parse import urlencode

from fastapi import Request

from .config import PROJECT_ROOT, Settings


class PhotoStorage(Protocol):
    def save(self, key: str, data: bytes) -> None: ...
    def delete(self, key: str) -> None: ...
    def signed_url(self, key: str) -> str: ...


def _signature(secret: str, key: str, expires: int) -> str:
    return hmac.new(secret.encode(), f"{key}:{expires}".encode(), hashlib.sha256).hexdigest()


class LocalStorage:
    def __init__(self, directory: Path, secret: str, ttl_seconds: int) -> None:
        self.directory = directory
        self.secret = secret
        self.ttl_seconds = ttl_seconds

    def _path(self, key: str) -> Path:
        path = (self.directory / key).resolve()
        if self.directory.resolve() not in path.parents:
            raise ValueError("invalid photo key")  # never escape the photo folder
        return path

    def save(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def signed_url(self, key: str) -> str:
        expires = int(time.time()) + self.ttl_seconds
        return f"/api/photos/{key}?" + urlencode({"exp": expires, "sig": _signature(self.secret, key, expires)})

    def read_signed(self, key: str, expires: int, signature: str) -> Path | None:
        """File behind a signed URL, or None if the signature is wrong or expired."""
        valid = hmac.compare_digest(signature, _signature(self.secret, key, expires))
        if not valid or expires < time.time():
            return None
        path = self._path(key)
        return path if path.is_file() else None


class S3Storage:
    def __init__(self, settings: Settings) -> None:
        import boto3  # only needed when S3 is configured

        self.bucket = settings.s3_bucket
        self.ttl_seconds = settings.photo_url_ttl_seconds
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            region_name=settings.s3_region or None,
            aws_access_key_id=settings.s3_access_key_id or None,
            aws_secret_access_key=settings.s3_secret_access_key or None,
        )

    def save(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType="image/jpeg")

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def signed_url(self, key: str) -> str:
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=self.ttl_seconds
        )


def make_storage(settings: Settings) -> PhotoStorage:
    if settings.photo_storage == "s3":
        return S3Storage(settings)
    directory = Path(settings.photo_dir) if settings.photo_dir else PROJECT_ROOT / "data" / "photos"
    return LocalStorage(directory, settings.jwt_secret, settings.photo_url_ttl_seconds)


def get_storage(request: Request) -> PhotoStorage:
    """Dependency: the photo storage of the running app."""
    return request.app.state.storage
