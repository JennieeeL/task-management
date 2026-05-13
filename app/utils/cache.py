import json
import hashlib
import logging
from flask import current_app
import redis

logger = logging.getLogger(__name__)

_redis_client = None


def _get_redis() -> redis.Redis | None:
    """Get or create Redis client. Returns None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        _redis_client = redis.from_url(url, decode_responses=True, socket_timeout=2)
        _redis_client.ping()
        return _redis_client
    except Exception:
        logger.warning("Redis unavailable — caching disabled")
        _redis_client = None
        return None


def make_cache_key(*parts) -> str:
    """Create a deterministic cache key from parts."""
    raw = ':'.join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()


def cache_get(key: str) -> dict | None:
    """Get a value from Redis cache. Returns None on miss or error."""
    client = _get_redis()
    if not client:
        return None
    try:
        data = client.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


def cache_set(key: str, value: dict, ttl: int = 300) -> None:
    """Set a value in Redis cache with TTL (seconds)."""
    client = _get_redis()
    if not client:
        return
    try:
        client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        logger.warning(f"Failed to set cache key: {key}")


def cache_delete(key: str) -> None:
    """Delete a specific cache key."""
    client = _get_redis()
    if not client:
        return
    try:
        client.delete(key)
    except Exception:
        pass


def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern (e.g., 'projects:*')."""
    client = _get_redis()
    if not client:
        return
    try:
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                client.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        logger.warning(f"Failed to delete cache pattern: {pattern}")
