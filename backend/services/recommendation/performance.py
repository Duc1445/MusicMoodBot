"""
=============================================================================
PERFORMANCE OPTIMIZATION LAYER
=============================================================================

Caching, precomputation, and query optimization for the recommendation engine.

Components:
===========
1. Multi-Level Cache
   - L1: In-memory LRU cache
   - L2: SQLite-based persistent cache
   
2. Precomputed Clusters
   - Emotion clusters (K-means on VA space)
   - Genre clusters
   - Artist similarity matrix
   
3. Query Optimization
   - Indexed queries
   - Batch operations
   - Connection pooling

Author: MusicMoodBot Team
Version: 4.0.0
=============================================================================
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable, TypeVar, Generic
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class CacheConfig:
    """Configuration for caching layer."""
    
    # L1 Cache (Memory)
    l1_max_size: int = 1000
    l1_ttl_seconds: float = 300.0  # 5 minutes
    
    # L2 Cache (Persistent)
    l2_enabled: bool = True
    l2_db_path: str = "cache.db"
    l2_ttl_seconds: float = 3600.0  # 1 hour
    l2_max_size: int = 10000
    
    # Precomputation
    cluster_update_interval_hours: int = 24
    similarity_matrix_size: int = 100
    
    # Query optimization
    batch_size: int = 100
    connection_pool_size: int = 5


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry."""
    key: str
    value: T
    created_at: datetime
    expires_at: datetime
    hits: int = 0
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'hits': self.hits,
        }


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'size': self.size,
            'hit_rate': round(self.hit_rate, 4),
        }


# =============================================================================
# LRU CACHE (L1 - MEMORY)
# =============================================================================

class LRUCache(Generic[T]):
    """
    Thread-safe LRU (Least Recently Used) cache.
    
    Features:
    - O(1) get and put operations
    - TTL support
    - Size-based eviction
    - Thread safety
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: float = 300.0
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats()
    
    def _compute_key(self, *args, **kwargs) -> str:
        """Compute cache key from arguments."""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats.misses += 1
                return None
            
            if entry.is_expired:
                del self._cache[key]
                self._stats.misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats.hits += 1
            
            return entry.value
    
    def put(self, key: str, value: T, ttl: float = None) -> None:
        """Put value in cache."""
        ttl = ttl or self.ttl_seconds
        
        with self._lock:
            # Remove if exists
            if key in self._cache:
                del self._cache[key]
            
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._stats.evictions += 1
            
            # Add new entry
            now = datetime.now()
            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl),
            )
            self._stats.size = len(self._cache)
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
            self._stats.size = 0
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                size=len(self._cache),
            )


# =============================================================================
# PERSISTENT CACHE (L2 - SQLITE)
# =============================================================================

class PersistentCache:
    """
    SQLite-based persistent cache for longer-term storage.
    
    Features:
    - Survives restarts
    - Configurable TTL
    - Automatic cleanup
    """
    
    def __init__(self, db_path: str, ttl_seconds: float = 3600.0, max_size: int = 10000):
        self.db_path = db_path
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._init_db()
    
    def _init_db(self):
        """Initialize cache database."""
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    hits INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
            conn.commit()
    
    @contextmanager
    def _connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from persistent cache."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            # Check expiration
            expires_at = datetime.fromisoformat(row['expires_at'])
            if datetime.now() > expires_at:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return None
            
            # Update hits
            conn.execute("UPDATE cache SET hits = hits + 1 WHERE key = ?", (key,))
            conn.commit()
            
            return json.loads(row['value'])
    
    def put(self, key: str, value: Any, ttl: float = None) -> None:
        """Put value in persistent cache."""
        ttl = ttl or self.ttl_seconds
        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl)
        
        with self._connection() as conn:
            # Enforce max size
            cursor = conn.execute("SELECT COUNT(*) as count FROM cache")
            count = cursor.fetchone()['count']
            
            if count >= self.max_size:
                # Delete oldest entries
                conn.execute("""
                    DELETE FROM cache
                    WHERE key IN (
                        SELECT key FROM cache
                        ORDER BY created_at ASC
                        LIMIT ?
                    )
                """, (count - self.max_size + 100,))
            
            # Insert or replace
            conn.execute("""
                INSERT OR REPLACE INTO cache (key, value, created_at, expires_at, hits)
                VALUES (?, ?, ?, ?, 0)
            """, (key, json.dumps(value), now.isoformat(), expires_at.isoformat()))
            
            conn.commit()
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._connection() as conn:
            cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
    
    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at < ?",
                (datetime.now().isoformat(),)
            )
            conn.commit()
            return cursor.rowcount
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._connection() as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as size,
                    SUM(hits) as total_hits
                FROM cache
            """)
            row = cursor.fetchone()
            
            return CacheStats(
                hits=row['total_hits'] or 0,
                size=row['size'] or 0,
            )


# =============================================================================
# MULTI-LEVEL CACHE
# =============================================================================

class MultiLevelCache:
    """
    Multi-level cache combining L1 (memory) and L2 (persistent).
    
    Lookup order:
    1. L1 (fast, small)
    2. L2 (slower, larger)
    
    On miss: Fetch and populate both levels
    On hit at L2: Promote to L1
    """
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        
        self.l1 = LRUCache(
            max_size=self.config.l1_max_size,
            ttl_seconds=self.config.l1_ttl_seconds,
        )
        
        self.l2 = None
        if self.config.l2_enabled:
            self.l2 = PersistentCache(
                db_path=self.config.l2_db_path,
                ttl_seconds=self.config.l2_ttl_seconds,
                max_size=self.config.l2_max_size,
            )
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 -> L2)."""
        # Try L1
        value = self.l1.get(key)
        if value is not None:
            return value
        
        # Try L2
        if self.l2:
            value = self.l2.get(key)
            if value is not None:
                # Promote to L1
                self.l1.put(key, value)
                return value
        
        return None
    
    def put(self, key: str, value: Any, ttl: float = None) -> None:
        """Put value in both cache levels."""
        self.l1.put(key, value, ttl or self.config.l1_ttl_seconds)
        
        if self.l2:
            self.l2.put(key, value, ttl or self.config.l2_ttl_seconds)
    
    def delete(self, key: str) -> bool:
        """Delete from both levels."""
        l1_deleted = self.l1.delete(key)
        l2_deleted = self.l2.delete(key) if self.l2 else False
        return l1_deleted or l2_deleted
    
    def clear(self) -> None:
        """Clear both levels."""
        self.l1.clear()
        if self.l2:
            self.l2.clear()
    
    def get_stats(self) -> Dict[str, CacheStats]:
        """Get statistics for both levels."""
        stats = {'l1': self.l1.get_stats()}
        if self.l2:
            stats['l2'] = self.l2.get_stats()
        return stats


# =============================================================================
# PRECOMPUTED CLUSTERS
# =============================================================================

@dataclass
class EmotionCluster:
    """A cluster of songs with similar emotional profiles."""
    cluster_id: int
    centroid_valence: float
    centroid_arousal: float
    song_ids: List[int]
    representative_mood: str
    
    def distance_to(self, valence: float, arousal: float) -> float:
        """Euclidean distance to a point."""
        return math.sqrt(
            (self.centroid_valence - valence) ** 2 +
            (self.centroid_arousal - arousal) ** 2
        )


class ClusterManager:
    """
    Manages precomputed emotion clusters for efficient retrieval.
    
    Uses simplified K-means clustering on VA space to group songs
    by emotional similarity. Clusters are precomputed and cached.
    """
    
    MOOD_CENTROIDS = {
        'happy': (0.8, 0.6),
        'sad': (-0.7, -0.3),
        'angry': (-0.6, 0.8),
        'calm': (0.5, -0.5),
        'excited': (0.7, 0.9),
        'peaceful': (0.6, -0.7),
        'anxious': (-0.3, 0.7),
        'melancholy': (-0.5, -0.4),
        'romantic': (0.6, 0.2),
        'energetic': (0.5, 0.9),
        'nostalgic': (0.1, -0.2),
        'neutral': (0.0, 0.0),
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.clusters: Dict[str, EmotionCluster] = {}
        self._last_update: Optional[datetime] = None
    
    @contextmanager
    def _connection(self):
        """Database connection context."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def build_clusters(self) -> None:
        """
        Build emotion clusters from song database.
        
        Assigns each song to the nearest mood centroid.
        """
        logger.info("Building emotion clusters...")
        
        with self._connection() as conn:
            cursor = conn.execute("""
                SELECT song_id, valence, energy as arousal, mood
                FROM songs
                WHERE valence IS NOT NULL OR mood IS NOT NULL
            """)
            
            # Initialize clusters
            clusters: Dict[str, List[int]] = {mood: [] for mood in self.MOOD_CENTROIDS}
            
            for row in cursor.fetchall():
                song_id = row['song_id']
                valence = row['valence'] or 0.0
                arousal = row['arousal'] or 0.0
                mood = (row['mood'] or 'neutral').lower()
                
                # If song has mood label, prefer that
                if mood in clusters:
                    clusters[mood].append(song_id)
                else:
                    # Find nearest centroid
                    min_dist = float('inf')
                    nearest_mood = 'neutral'
                    
                    for m, (cv, ca) in self.MOOD_CENTROIDS.items():
                        dist = math.sqrt((valence - cv) ** 2 + (arousal - ca) ** 2)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_mood = m
                    
                    clusters[nearest_mood].append(song_id)
            
            # Create EmotionCluster objects
            for i, (mood, song_ids) in enumerate(clusters.items()):
                cv, ca = self.MOOD_CENTROIDS[mood]
                self.clusters[mood] = EmotionCluster(
                    cluster_id=i,
                    centroid_valence=cv,
                    centroid_arousal=ca,
                    song_ids=song_ids,
                    representative_mood=mood,
                )
        
        self._last_update = datetime.now()
        logger.info(f"Built {len(self.clusters)} clusters with "
                   f"{sum(len(c.song_ids) for c in self.clusters.values())} songs")
    
    def get_cluster(self, mood: str) -> Optional[EmotionCluster]:
        """Get cluster for a mood."""
        return self.clusters.get(mood.lower())
    
    def get_nearest_cluster(self, valence: float, arousal: float) -> EmotionCluster:
        """Get cluster nearest to VA coordinates."""
        min_dist = float('inf')
        nearest = list(self.clusters.values())[0]
        
        for cluster in self.clusters.values():
            dist = cluster.distance_to(valence, arousal)
            if dist < min_dist:
                min_dist = dist
                nearest = cluster
        
        return nearest
    
    def get_candidate_songs(
        self,
        mood: str = None,
        valence: float = None,
        arousal: float = None,
        limit: int = 100
    ) -> List[int]:
        """
        Get candidate song IDs for recommendation.
        
        Efficiently retrieves songs from relevant clusters.
        """
        if not self.clusters:
            self.build_clusters()
        
        if mood:
            cluster = self.get_cluster(mood)
        elif valence is not None and arousal is not None:
            cluster = self.get_nearest_cluster(valence, arousal)
        else:
            # Return from all clusters
            all_ids = []
            for c in self.clusters.values():
                all_ids.extend(c.song_ids[:limit // len(self.clusters)])
            return all_ids[:limit]
        
        if cluster:
            return cluster.song_ids[:limit]
        
        return []


# =============================================================================
# QUERY OPTIMIZER
# =============================================================================

class QueryOptimizer:
    """
    Query optimization utilities for database operations.
    
    Features:
    - Batch operations
    - Indexed query helpers
    - Connection pooling
    """
    
    def __init__(self, db_path: str, config: CacheConfig = None):
        self.db_path = db_path
        self.config = config or CacheConfig()
        self._pool: List[sqlite3.Connection] = []
        self._pool_lock = threading.Lock()
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool."""
        conn = None
        
        with self._pool_lock:
            if self._pool:
                conn = self._pool.pop()
        
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
        
        try:
            yield conn
        finally:
            with self._pool_lock:
                if len(self._pool) < self.config.connection_pool_size:
                    self._pool.append(conn)
                else:
                    conn.close()
    
    def batch_fetch_songs(self, song_ids: List[int]) -> List[Dict]:
        """Efficiently fetch multiple songs by ID."""
        if not song_ids:
            return []
        
        results = []
        
        # Process in batches
        for i in range(0, len(song_ids), self.config.batch_size):
            batch_ids = song_ids[i:i + self.config.batch_size]
            placeholders = ','.join('?' * len(batch_ids))
            
            with self.get_connection() as conn:
                cursor = conn.execute(f"""
                    SELECT *
                    FROM songs
                    WHERE song_id IN ({placeholders})
                """, batch_ids)
                
                results.extend([dict(row) for row in cursor.fetchall()])
        
        return results
    
    def create_indexes(self) -> None:
        """Create recommended indexes for performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_songs_mood ON songs(mood)",
            "CREATE INDEX IF NOT EXISTS idx_songs_genre ON songs(genre)",
            "CREATE INDEX IF NOT EXISTS idx_songs_valence_energy ON songs(valence, energy)",
            "CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id, feedback_type)",
            "CREATE INDEX IF NOT EXISTS idx_history_user_time ON listening_history(user_id, listened_at)",
            "CREATE INDEX IF NOT EXISTS idx_history_session ON listening_history(session_id)",
        ]
        
        with self.get_connection() as conn:
            for idx in indexes:
                try:
                    conn.execute(idx)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")
            conn.commit()
        
        logger.info("Database indexes created/verified")


# =============================================================================
# CACHING DECORATOR
# =============================================================================

def cached(
    cache: MultiLevelCache,
    ttl: float = None,
    key_prefix: str = ""
):
    """
    Decorator to cache function results.
    
    Usage:
        cache = MultiLevelCache()
        
        @cached(cache, ttl=300, key_prefix="recommendations")
        def get_recommendations(user_id, mood):
            # Expensive computation
            return recommendations
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            key_data = json.dumps({
                'prefix': key_prefix,
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs,
            }, sort_keys=True, default=str)
            key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.put(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# =============================================================================
# PERFORMANCE MONITOR
# =============================================================================

class PerformanceMonitor:
    """
    Monitors and tracks performance metrics.
    """
    
    def __init__(self):
        self._timings: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    @contextmanager
    def measure(self, operation: str):
        """Context manager to measure operation time."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            with self._lock:
                self._timings[operation].append(elapsed)
    
    def record(self, operation: str, duration: float):
        """Record a timing measurement."""
        with self._lock:
            self._timings[operation].append(duration)
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics."""
        stats = {}
        
        with self._lock:
            for op, timings in self._timings.items():
                if timings:
                    stats[op] = {
                        'count': len(timings),
                        'mean_ms': sum(timings) / len(timings) * 1000,
                        'min_ms': min(timings) * 1000,
                        'max_ms': max(timings) * 1000,
                        'p95_ms': sorted(timings)[int(len(timings) * 0.95)] * 1000,
                    }
        
        return stats
    
    def clear(self):
        """Clear all measurements."""
        with self._lock:
            self._timings.clear()


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_cache(config: CacheConfig = None) -> MultiLevelCache:
    """Create a MultiLevelCache instance."""
    return MultiLevelCache(config or CacheConfig())


def create_cluster_manager(db_path: str) -> ClusterManager:
    """Create a ClusterManager instance."""
    return ClusterManager(db_path)


def create_query_optimizer(db_path: str, config: CacheConfig = None) -> QueryOptimizer:
    """Create a QueryOptimizer instance."""
    return QueryOptimizer(db_path, config)
