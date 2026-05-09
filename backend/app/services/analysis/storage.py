"""
Chart storage abstraction layer.
Supports local filesystem and S3 backends via a common interface.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChartStorageBackend(ABC):
    """Abstract storage backend for chart assets."""

    @abstractmethod
    def save_json(self, job_id: str, chart_id: str, data: Dict[str, Any]) -> str:
        """Save chart data as JSON. Returns the storage path / URL."""

    @abstractmethod
    def save_png(self, job_id: str, chart_id: str, image_bytes: bytes) -> str:
        """Save chart as PNG. Returns the storage path / URL."""

    @abstractmethod
    def get_public_url(self, path: str) -> str:
        """Return a publicly accessible URL for the stored asset."""


class LocalFileSystemBackend(ChartStorageBackend):
    """Store charts on the local filesystem (default)."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or settings.analysis_chart_dir

    def _ensure_dir(self, job_id: str) -> str:
        path = os.path.join(self.base_dir, job_id)
        os.makedirs(path, exist_ok=True)
        return path

    def save_json(self, job_id: str, chart_id: str, data: Dict[str, Any]) -> str:
        out_dir = self._ensure_dir(job_id)
        filepath = os.path.join(out_dir, f"{chart_id}.json")
        with open(filepath, "w") as f:
            json.dump(data, f)
        logger.debug("Chart JSON saved: %s", filepath)
        return filepath

    def save_png(self, job_id: str, chart_id: str, image_bytes: bytes) -> str:
        out_dir = self._ensure_dir(job_id)
        filepath = os.path.join(out_dir, f"{chart_id}.png")
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        logger.debug("Chart PNG saved: %s", filepath)
        return filepath

    def get_public_url(self, path: str) -> str:
        return path  # Local filesystem — path is the reference


class S3Backend(ChartStorageBackend):
    """Store charts in S3-compatible storage."""

    def __init__(self):
        import boto3  # type: ignore[import-untyped]

        self.bucket = settings.analysis_s3_bucket
        self.prefix = settings.analysis_s3_prefix or "analysis_charts/"
        self.endpoint_url = settings.analysis_s3_endpoint or None
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.analysis_s3_access_key or None,
            aws_secret_access_key=settings.analysis_s3_secret_key or None,
        )

    def _key(self, job_id: str, filename: str) -> str:
        return f"{self.prefix.rstrip('/')}/{job_id}/{filename}"

    def save_json(self, job_id: str, chart_id: str, data: Dict[str, Any]) -> str:
        import io
        import json

        key = self._key(job_id, f"{chart_id}.json")
        buf = io.BytesIO(json.dumps(data).encode("utf-8"))
        self.client.upload_fileobj(buf, self.bucket, key, ExtraArgs={"ContentType": "application/json"})
        logger.debug("Chart JSON uploaded to S3: %s/%s", self.bucket, key)
        return f"s3://{self.bucket}/{key}"

    def save_png(self, job_id: str, chart_id: str, image_bytes: bytes) -> str:
        import io

        key = self._key(job_id, f"{chart_id}.png")
        buf = io.BytesIO(image_bytes)
        self.client.upload_fileobj(buf, self.bucket, key, ExtraArgs={"ContentType": "image/png"})
        logger.debug("Chart PNG uploaded to S3: %s/%s", self.bucket, key)
        return f"s3://{self.bucket}/{key}"

    def get_public_url(self, path: str) -> str:
        if self.endpoint_url:
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket}/{path.removeprefix(f's3://{self.bucket}/')}"
        return f"https://{self.bucket}.s3.amazonaws.com/{path.removeprefix(f's3://{self.bucket}/')}"


_storage: ChartStorageBackend | None = None


def get_chart_storage() -> ChartStorageBackend:
    """Factory for the configured chart storage backend."""
    global _storage
    if _storage is None:
        backend = settings.analysis_storage_backend
        if backend == "s3":
            _storage = S3Backend()
        else:
            _storage = LocalFileSystemBackend()
    return _storage
