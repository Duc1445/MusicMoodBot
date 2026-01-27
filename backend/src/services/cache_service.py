"""
Caching service for API responses and expensive computations.
Supports TTL-based expiration and LRU eviction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from collections import OrderedDict
from functools import wraps
import threading
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Single cache entry with metadata."""
    value: T
    created_at: datetime
    expires_at: Optional[datetime]
    hits: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def access(self) -> T:
        """Record access and return value."""
        self.hits += 1
        self.last_accessed = datetime.now()
        return self.value


class LRUCache:
    """
    Thread-safe LRU cache with TTL support.
    
    Features:
    - Automatic expiration based on TTL
    - LRU eviction when max size reached
    - Thread-safe operations
    - Hit/miss statistics
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 300,  # 5 minutes
        name: str = "default"
    ):
        self.max_size = max_size
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        self.name = name
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.access()
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache."""
        with self._lock:
            # Check max size
            while len(self._cache) >= self.max_size:
                # Evict oldest (least recently used)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._evictions += 1
            
            # Calculate expiration
            ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else self.default_ttl
            expires_at = datetime.now() + ttl if ttl else None
            
            # Create entry
            entry = CacheEntry(
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> int:
        """Clear all entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "name": self.name,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "evictions": self._evictions,
                "default_ttl_seconds": self.default_ttl.total_seconds()
            }


# Global cache instances
_caches: Dict[str, LRUCache] = {}
_cache_lock = threading.Lock()


def get_cache(
    name: str = "default",
    max_size: int = 1000,
    default_ttl_seconds: int = 300
) -> LRUCache:
    """Get or create a named cache instance."""
    with _cache_lock:
        if name not in _caches:
            _caches[name] = LRUCache(
                max_size=max_size,
                default_ttl_seconds=default_ttl_seconds,
                name=name
            )
        return _caches[name]


def cached(
    cache_name: str = "default",
    ttl_seconds: Optional[int] = None,
    key_prefix: str = ""
) -> Callable:
    """
    Decorator to cache function results.
    
    Usage:
        @cached(cache_name="songs", ttl_seconds=60)
        def get_songs_by_mood(mood: str) -> List[Song]:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache(cache_name)
            
            # Generate key
            key_parts = [key_prefix, func.__name__] if key_prefix else [func.__name__]
            key_data = json.dumps({
                "prefix": key_parts,
                "args": args,
                "kwargs": kwargs
            }, sort_keys=True, default=str)
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache HIT: {func.__name__}")
                return result
            
            # Compute and cache
            logger.debug(f"Cache MISS: {func.__name__}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result
        
        return wrapper
    return decorator


def invalidate_cache(cache_name: str = "default", pattern: str = None) -> int:
    """Invalidate cache entries matching pattern."""
    cache = get_cache(cache_name)
    if pattern is None:
        return cache.clear()
    
    # Pattern-based invalidation (simple prefix match)
    count = 0
    with cache._lock:
        keys_to_delete = [
            key for key in cache._cache.keys()
            if pattern in key
        ]
        for key in keys_to_delete:
            del cache._cache[key]
            count += 1
    return count


def get_all_cache_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all caches."""
    with _cache_lock:
        return {name: cache.stats for name, cache in _caches.items()}


# ==================== SPECIALIZED CACHES ====================

# Song cache (longer TTL)
song_cache = get_cache("songs", max_size=500, default_ttl_seconds=600)

# Search cache (shorter TTL)
search_cache = get_cache("search", max_size=200, default_ttl_seconds=120)

# Recommendation cache (medium TTL)
recommendation_cache = get_cache("recommendations", max_size=300, default_ttl_seconds=300)

# User preference cache
user_cache = get_cache("users", max_size=100, default_ttl_seconds=900)


# ==================== UTILITY FUNCTIONS ====================

def cache_song_list(songs: list, mood: str = None) -> None:
    """Cache a list of songs with optional mood key."""
    key = f"songs_{mood}" if mood else "songs_all"
    song_cache.set(key, songs)


def get_cached_songs(mood: str = None) -> Optional[list]:
    """Get cached song list."""
    key = f"songs_{mood}" if mood else "songs_all"
    return song_cache.get(key)


def cache_search_results(query: str, results: list) -> None:
    """Cache search results."""
    key = hashlib.md5(query.lower().encode()).hexdigest()
    search_cache.set(key, results)


def get_cached_search(query: str) -> Optional[list]:
    """Get cached search results."""
    key = hashlib.md5(query.lower().encode()).hexdigest()
    return search_cache.get(key)
