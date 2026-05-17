"""Sibyl — Disk-based response cache."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import diskcache

from sibyl.config import get_settings

logger = logging.getLogger(__name__)

_cache: diskcache.Cache | None = None


def _get_cache() -> diskcache.Cache:
    """Lazily initialize the disk cache."""
    global _cache
    if _cache is None:
        settings = get_settings()
        _cache = diskcache.Cache(settings.cache_dir)
        logger.info("Cache initialized at %s", settings.cache_dir)
    return _cache


def cache_key(prefix: str, data: dict | str) -> str:
    """Generate a deterministic cache key."""
    raw = json.dumps(data, sort_keys=True) if isinstance(data, dict) else data
    return f"{prefix}:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


def get_cached(key: str) -> Any | None:
    """Retrieve a cached value, or None if not found / expired."""
    try:
        cache = _get_cache()
        return cache.get(key)
    except Exception:
        return None


def set_cached(key: str, value: Any, ttl: int = 300) -> None:
    """Store a value in the cache with TTL (default 5 minutes)."""
    try:
        cache = _get_cache()
        cache.set(key, value, expire=ttl)
    except Exception as _err:
        logger.warning("Cache write failed: %s", _err)
