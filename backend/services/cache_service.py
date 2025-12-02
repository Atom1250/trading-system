"""Simple in-memory caching layer."""
from datetime import datetime, timedelta
from typing import Optional, Any
from cachetools import TTLCache
import hashlib
import json


class CacheService:
    """Simple TTL-based cache service."""
    
    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            maxsize: Maximum number of items in cache
            ttl: Time-to-live in seconds (default 1 hour)
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set item in cache."""
        self._cache[key] = value
    
    def delete(self, key: str) -> None:
        """Delete item from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()
    
    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = {
            "args": args,
            "kwargs": {k: str(v) for k, v in kwargs.items()}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()


# Global cache instance
cache = CacheService()
