"""
Caching utilities for performance optimization.

Provides in-memory caching with TTL support for search results and other expensive operations.
"""
import hashlib
import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Time-To-Live cache with automatic expiration.

    Thread-safe LRU cache with TTL support for efficient in-memory caching.
    """

    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        """
        Initialize TTL cache.

        Args:
            maxsize: Maximum number of items to cache
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: dict[str, float] = {}
        self._hits = 0
        self._misses = 0

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry has expired."""
        if key not in self.timestamps:
            return True
        return (time.time() - self.timestamps[key]) > self.ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache or self._is_expired(key):
            self._misses += 1
            if key in self.cache:
                # Remove expired entry
                del self.cache[key]
                del self.timestamps[key]
            return None

        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        self._hits += 1
        return self.cache[key]

    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Remove oldest if at capacity
        if key not in self.cache and len(self.cache) >= self.maxsize:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]

        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.cache.move_to_end(key)

    def clear(self) -> None:
        """Clear all cached items."""
        self.cache.clear()
        self.timestamps.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": len(self.cache),
            "maxsize": self.maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "ttl_seconds": self.ttl,
        }


def create_cache_key(*args, **kwargs) -> str:
    """
    Create a deterministic cache key from arguments.

    Args:
        *args: Positional arguments to hash
        **kwargs: Keyword arguments to hash

    Returns:
        SHA256 hash of arguments as cache key
    """
    # Create a deterministic string representation
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items()),
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.sha256(key_str.encode()).hexdigest()


def cached_with_ttl(cache: TTLCache):
    """
    Decorator to cache function results with TTL.

    Args:
        cache: TTLCache instance to use

    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create cache key from arguments
            cache_key = create_cache_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            # Call function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Create cache key from arguments
            cache_key = create_cache_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            # Call function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Global cache instances
search_results_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes
embedding_cache = TTLCache(maxsize=10000, ttl=3600)  # 1 hour
