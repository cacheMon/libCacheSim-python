"""S3 Bucket data loader with local caching (HuggingFace-style)."""

from __future__ import annotations

import logging
import os
import re
import shutil
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class _DataLoader:
    """Internal S3 data loader with local caching."""

    DEFAULT_BUCKET = "cache-datasets"
    DEFAULT_CACHE_DIR = Path(os.environ.get("LCS_HUB_CACHE", Path.home() / ".cache/libcachesim/hub"))

    # Characters that are problematic on various filesystems
    INVALID_CHARS = set('<>:"|?*\x00')
    # Reserved names on Windows
    RESERVED_NAMES = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    def __init__(
        self, bucket_name: str = DEFAULT_BUCKET, cache_dir: Optional[Union[str, Path]] = None, use_auth: bool = False
    ):
        self.bucket_name = self._validate_bucket_name(bucket_name)
        self.cache_dir = Path(cache_dir) if cache_dir else self.DEFAULT_CACHE_DIR
        self.use_auth = use_auth
        self._s3_client = None
        self._ensure_cache_dir()

    def _validate_bucket_name(self, bucket_name: str) -> str:
        """Validate S3 bucket name according to AWS rules."""
        if not bucket_name:
            raise ValueError("Bucket name cannot be empty")

        if len(bucket_name) < 3 or len(bucket_name) > 63:
            raise ValueError("Bucket name must be between 3 and 63 characters")

        if not re.match(r"^[a-z0-9.-]+$", bucket_name):
            raise ValueError("Bucket name can only contain lowercase letters, numbers, periods, and hyphens")

        if bucket_name.startswith(".") or bucket_name.endswith("."):
            raise ValueError("Bucket name cannot start or end with a period")

        if bucket_name.startswith("-") or bucket_name.endswith("-"):
            raise ValueError("Bucket name cannot start or end with a hyphen")

        if ".." in bucket_name:
            raise ValueError("Bucket name cannot contain consecutive periods")

        return bucket_name

    def _validate_and_sanitize_key(self, key: str) -> str:
        """Validate and sanitize S3 key for safe local filesystem usage."""
        if not key:
            raise ValueError("S3 key cannot be empty")

        if len(key) > 1024:  # S3 limit is 1024 bytes
            raise ValueError("S3 key is too long (max 1024 characters)")

        # Check for path traversal attempts
        if ".." in key:
            raise ValueError("S3 key cannot contain '..' (path traversal not allowed)")

        if key.startswith("/"):
            raise ValueError("S3 key cannot start with '/'")

        # Split key into parts and validate each part
        parts = key.split("/")
        sanitized_parts = []

        for part in parts:
            if not part:  # Empty part (double slash)
                continue

            # Check for reserved names (case insensitive)
            if part.upper() in self.RESERVED_NAMES:
                raise ValueError(f"S3 key contains reserved name: {part}")

            # Check for invalid characters
            if any(c in self.INVALID_CHARS for c in part):
                raise ValueError(f"S3 key contains invalid characters in part: {part}")

            # Check if part is too long for filesystem
            if len(part) > 255:  # Most filesystems have 255 char limit per component
                raise ValueError(f"S3 key component too long: {part}")

            sanitized_parts.append(part)

        if not sanitized_parts:
            raise ValueError("S3 key resulted in empty path after sanitization")

        return "/".join(sanitized_parts)

    def _ensure_cache_dir(self) -> None:
        (self.cache_dir / self.bucket_name).mkdir(parents=True, exist_ok=True)

    def _get_available_disk_space(self, path: Path) -> int:
        """Get available disk space in bytes."""
        try:
            stat = os.statvfs(path)
            return stat.f_bavail * stat.f_frsize
        except (OSError, AttributeError):
            # Fallback for Windows or other systems
            try:
                import shutil

                return shutil.disk_usage(path).free
            except Exception:
                logger.warning("Could not determine available disk space")
                return float("inf")  # Assume unlimited space if we can't check

    @property
    def s3_client(self):
        if self._s3_client is None:
            try:
                import boto3
                from botocore.config import Config
                from botocore import UNSIGNED

                self._s3_client = boto3.client(
                    "s3", config=None if self.use_auth else Config(signature_version=UNSIGNED)
                )
            except ImportError:
                raise ImportError("Install boto3: pip install boto3")
        return self._s3_client

    def _cache_path(self, key: str) -> Path:
        """Create cache path that mirrors S3 structure after validation."""
        sanitized_key = self._validate_and_sanitize_key(key)
        cache_path = self.cache_dir / self.bucket_name / sanitized_key

        # Double-check that the resolved path is still within cache directory
        try:
            cache_path.resolve().relative_to(self.cache_dir.resolve())
        except ValueError:
            raise ValueError(f"S3 key resolves outside cache directory: {key}")

        return cache_path

    def _get_object_size(self, key: str) -> int:
        """Get the size of an S3 object without downloading it."""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return response["ContentLength"]
        except Exception as e:
            logger.warning(f"Could not determine object size for s3://{self.bucket_name}/{key}: {e}")
            return 0

    def _download(self, key: str, dest: Path) -> None:
        temp = dest.with_suffix(dest.suffix + ".tmp")
        temp.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Check available disk space before downloading
            object_size = self._get_object_size(key)
            if object_size > 0:
                available_space = self._get_available_disk_space(temp.parent)
                if object_size > available_space:
                    raise RuntimeError(
                        f"Insufficient disk space. Need {object_size / (1024**3):.2f} GB, "
                        f"but only {available_space / (1024**3):.2f} GB available"
                    )

            logger.info(f"Downloading s3://{self.bucket_name}/{key}")
            obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            with open(temp, "wb") as f:
                f.write(obj["Body"].read())
            shutil.move(str(temp), str(dest))
            logger.info(f"Saved to: {dest}")
        except Exception as e:
            if temp.exists():
                temp.unlink()
            raise RuntimeError(f"Download failed for s3://{self.bucket_name}/{key}: {e}")

    def load(self, key: str, force: bool = False, mode: str = "rb") -> Union[bytes, str]:
        path = self._cache_path(key)
        if not path.exists() or force:
            self._download(key, path)
        with open(path, mode) as f:
            return f.read()

    def get_cached_path(self, key: str) -> str:
        """Get the local cached file path, downloading if necessary."""
        path = self._cache_path(key)
        if not path.exists():
            self._download(key, path)
        return str(path)

    def is_cached(self, key: str) -> bool:
        try:
            return self._cache_path(key).exists()
        except ValueError:
            return False

    def clear_cache(self, key: Optional[str] = None) -> None:
        if key:
            try:
                path = self._cache_path(key)
                if path.exists():
                    path.unlink()
                    logger.info(f"Cleared: {path}")
            except ValueError as e:
                logger.warning(f"Cannot clear cache for invalid key {key}: {e}")
        else:
            shutil.rmtree(self.cache_dir, ignore_errors=True)
            logger.info(f"Cleared entire cache: {self.cache_dir}")

    def list_cached_files(self) -> list[str]:
        if not self.cache_dir.exists():
            return []
        return [str(p) for p in self.cache_dir.rglob("*") if p.is_file() and not p.name.endswith(".tmp")]

    def get_cache_size(self) -> int:
        return sum(p.stat().st_size for p in self.cache_dir.rglob("*") if p.is_file())

    def list_s3_objects(self, prefix: str = "", delimiter: str = "/") -> dict:
        """
        List S3 objects and pseudo-folders under a prefix.

        Args:
            prefix: The S3 prefix to list under (like folder path)
            delimiter: Use "/" to simulate folder structure

        Returns:
            A dict with two keys:
                - "folders": list of sub-prefixes (folders)
                - "files": list of object keys (files)
        """
        paginator = self.s3_client.get_paginator("list_objects_v2")
        result = {"folders": [], "files": []}

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix, Delimiter=delimiter):
            # CommonPrefixes are like subdirectories
            result["folders"].extend(cp["Prefix"] for cp in page.get("CommonPrefixes", []))
            result["files"].extend(obj["Key"] for obj in page.get("Contents", []))

        return result


# Global data loader instance
_data_loader = _DataLoader()


def set_cache_dir(cache_dir: Union[str, Path]) -> None:
    """
    Set the global cache directory for S3 downloads.

    Args:
        cache_dir: Path to the cache directory

    Example:
        >>> import libcachesim as lcs
        >>> lcs.set_cache_dir("/tmp/my_cache")
    """
    global _data_loader
    _data_loader = _DataLoader(cache_dir=cache_dir)


def get_cache_dir() -> Path:
    """
    Get the current cache directory.

    Returns:
        Path to the current cache directory

    Example:
        >>> import libcachesim as lcs
        >>> print(lcs.get_cache_dir())
        /home/user/.cache/libcachesim/hub
    """
    return _data_loader.cache_dir


def clear_cache(s3_path: Optional[str] = None) -> None:
    """
    Clear cached files.

    Args:
        s3_path: Specific S3 path to clear, or None to clear all cache

    Example:
        >>> import libcachesim as lcs
        >>> # Clear specific file
        >>> lcs.clear_cache("s3://cache-datasets/trace1.lcs.zst")
        >>> # Clear all cache
        >>> lcs.clear_cache()
    """
    if s3_path and s3_path.startswith("s3://"):
        parsed = urlparse(s3_path)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        if bucket == _data_loader.bucket_name:
            _data_loader.clear_cache(key)
        else:
            logger.warning(f"Cannot clear cache for different bucket: {bucket}")
    else:
        _data_loader.clear_cache(s3_path)


def get_cache_size() -> int:
    """
    Get total size of cached files in bytes.

    Returns:
        Total cache size in bytes

    Example:
        >>> import libcachesim as lcs
        >>> size_mb = lcs.get_cache_size() / (1024**2)
        >>> print(f"Cache size: {size_mb:.2f} MB")
    """
    return _data_loader.get_cache_size()


def list_cached_files() -> list[str]:
    """
    List all cached files.

    Returns:
        List of cached file paths

    Example:
        >>> import libcachesim as lcs
        >>> files = lcs.list_cached_files()
        >>> for file in files:
        ...     print(file)
    """
    return _data_loader.list_cached_files()


def get_data_loader(bucket_name: str = None) -> _DataLoader:
    """Get data loader instance for a specific bucket or the global one."""
    global _data_loader
    if bucket_name is None or bucket_name == _data_loader.bucket_name:
        return _data_loader
    else:
        return _DataLoader(bucket_name=bucket_name, cache_dir=_data_loader.cache_dir.parent)
