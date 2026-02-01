"""
Database connection pooling and query optimization utilities.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Callable
from contextlib import contextmanager
from dataclasses import dataclass
import sqlite3
import threading
import logging
import time
import os

from backend.src.services.constants import TABLE_SONGS

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """Statistics for connection pool."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_queries: int = 0
    total_query_time_ms: float = 0.0
    
    @property
    def avg_query_time_ms(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.total_query_time_ms / self.total_queries


class ConnectionPool:
    """
    Thread-safe SQLite connection pool.
    
    Features:
    - Connection reuse
    - Thread-local connections
    - Query timing
    - Automatic cleanup
    """
    
    def __init__(
        self,
        db_path: str,
        max_connections: int = 10,
        timeout_seconds: float = 30.0
    ):
        self.db_path = db_path
        self.max_connections = max_connections
        self.timeout = timeout_seconds
        
        self._pool: List[sqlite3.Connection] = []
        self._lock = threading.Lock()
        self._local = threading.local()
        self._stats = ConnectionStats()
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        con = sqlite3.connect(
            self.db_path,
            timeout=self.timeout,
            check_same_thread=False
        )
        con.row_factory = sqlite3.Row
        
        # Enable optimizations
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        con.execute("PRAGMA cache_size=10000")
        con.execute("PRAGMA temp_store=MEMORY")
        
        self._stats.total_connections += 1
        return con
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool or create new one."""
        # Check thread-local first
        if hasattr(self._local, 'connection') and self._local.connection:
            return self._local.connection
        
        with self._lock:
            if self._pool:
                con = self._pool.pop()
                self._stats.idle_connections -= 1
            else:
                con = self._create_connection()
            
            self._stats.active_connections += 1
        
        self._local.connection = con
        return con
    
    def release_connection(self, con: sqlite3.Connection) -> None:
        """Release a connection back to the pool."""
        with self._lock:
            self._stats.active_connections -= 1
            
            if len(self._pool) < self.max_connections:
                self._pool.append(con)
                self._stats.idle_connections += 1
            else:
                con.close()
        
        if hasattr(self._local, 'connection'):
            self._local.connection = None
    
    @contextmanager
    def connection(self):
        """Context manager for getting a connection."""
        con = self.get_connection()
        try:
            yield con
        finally:
            self.release_connection(con)
    
    def execute(
        self,
        query: str,
        params: tuple = (),
        fetch: bool = True
    ) -> Optional[List[Dict]]:
        """Execute a query with timing."""
        start = time.time()
        
        con = self.get_connection()
        try:
            cur = con.cursor()
            cur.execute(query, params)
            
            if fetch:
                result = [dict(row) for row in cur.fetchall()]
            else:
                con.commit()
                result = None
        finally:
            elapsed_ms = (time.time() - start) * 1000
            self._stats.total_queries += 1
            self._stats.total_query_time_ms += elapsed_ms
            
            if elapsed_ms > 100:
                logger.warning(f"Slow query ({elapsed_ms:.1f}ms): {query[:100]}")
            
            self.release_connection(con)
        
        return result
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            for con in self._pool:
                con.close()
            self._pool.clear()
            self._stats.idle_connections = 0
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "total_connections": self._stats.total_connections,
            "active_connections": self._stats.active_connections,
            "idle_connections": self._stats.idle_connections,
            "pool_size": len(self._pool),
            "total_queries": self._stats.total_queries,
            "avg_query_time_ms": round(self._stats.avg_query_time_ms, 2)
        }


# Global connection pools
_pools: Dict[str, ConnectionPool] = {}
_pools_lock = threading.Lock()


def get_pool(db_path: str) -> ConnectionPool:
    """Get or create a connection pool for a database."""
    with _pools_lock:
        if db_path not in _pools:
            _pools[db_path] = ConnectionPool(db_path)
        return _pools[db_path]


# ==================== OPTIMIZED QUERY FUNCTIONS ====================

class OptimizedSongRepo:
    """
    Optimized song repository with caching and batch operations.
    """
    
    def __init__(self, db_path: str):
        self.pool = get_pool(db_path)
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, float] = {}
        self._cache_ttl = 60.0  # 60 seconds
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache_time:
            return False
        return (time.time() - self._cache_time[key]) < self._cache_ttl
    
    def _set_cache(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._cache_time[key] = time.time()
    
    def fetch_all_songs(self, force_refresh: bool = False) -> List[Dict]:
        """Fetch all songs with caching."""
        cache_key = "all_songs"
        
        if not force_refresh and self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        result = self.pool.execute(f"SELECT * FROM {TABLE_SONGS}")
        self._set_cache(cache_key, result)
        return result
    
    def fetch_songs_by_mood(self, mood: str) -> List[Dict]:
        """Fetch songs by mood with caching."""
        cache_key = f"songs_mood_{mood}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        result = self.pool.execute(
            f"SELECT * FROM {TABLE_SONGS} WHERE mood = ?",
            (mood,)
        )
        self._set_cache(cache_key, result)
        return result
    
    def fetch_songs_by_ids(self, song_ids: List[int]) -> List[Dict]:
        """Fetch multiple songs by IDs efficiently."""
        if not song_ids:
            return []
        
        placeholders = ",".join("?" * len(song_ids))
        return self.pool.execute(
            f"SELECT * FROM {TABLE_SONGS} WHERE song_id IN ({placeholders})",
            tuple(song_ids)
        )
    
    def search_songs(
        self,
        query: str,
        mood: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Optimized text search with optional mood filter.
        Uses LIKE for simple search, consider FTS for production.
        """
        conditions = []
        params = []
        
        if query:
            conditions.append(
                "(song_name LIKE ? OR artist LIKE ? OR genre LIKE ?)"
            )
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query])
        
        if mood:
            conditions.append("mood = ?")
            params.append(mood)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        return self.pool.execute(
            f"""
            SELECT * FROM {TABLE_SONGS}
            WHERE {where_clause}
            ORDER BY mood_score DESC
            LIMIT ?
            """,
            (*params, limit)
        )
    
    def get_song_stats(self) -> Dict[str, Any]:
        """Get song statistics efficiently."""
        cache_key = "song_stats"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        # Single query for multiple stats
        result = self.pool.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN mood IS NOT NULL THEN 1 END) as with_mood,
                AVG(energy) as avg_energy,
                AVG(happiness) as avg_happiness,
                AVG(tempo) as avg_tempo,
                MIN(tempo) as min_tempo,
                MAX(tempo) as max_tempo
            FROM songs
        """)
        
        if result:
            stats = result[0]
            self._set_cache(cache_key, stats)
            return stats
        
        return {}
    
    def get_mood_distribution(self) -> Dict[str, int]:
        """Get mood distribution efficiently."""
        result = self.pool.execute("""
            SELECT mood, COUNT(*) as count
            FROM songs
            WHERE mood IS NOT NULL
            GROUP BY mood
        """)
        
        return {row["mood"]: row["count"] for row in (result or [])}
    
    def batch_update_moods(
        self,
        updates: List[Dict[str, Any]]
    ) -> int:
        """
        Batch update song moods efficiently.
        
        Args:
            updates: List of {song_id, mood, intensity, mood_score, ...}
            
        Returns:
            Number of updated rows
        """
        if not updates:
            return 0
        
        with self.pool.connection() as con:
            cur = con.cursor()
            count = 0
            
            for update in updates:
                song_id = update.pop("song_id", None)
                if not song_id:
                    continue
                
                if update:
                    cols = list(update.keys())
                    set_clause = ", ".join([f"{c}=?" for c in cols])
                    vals = [update[c] for c in cols] + [song_id]
                    
                    cur.execute(
                        f"UPDATE {TABLE_SONGS} SET {set_clause} WHERE song_id=?",
                        vals
                    )
                    count += cur.rowcount
            
            con.commit()
        
        # Invalidate cache
        self._cache.clear()
        self._cache_time.clear()
        
        return count
    
    def invalidate_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._cache_time.clear()


# ==================== QUERY BUILDER ====================

class QueryBuilder:
    """
    Fluent query builder for complex queries.
    """
    
    def __init__(self, table: str = TABLE_SONGS):
        self.table = table
        self._select = ["*"]
        self._where: List[str] = []
        self._params: List[Any] = []
        self._order_by: Optional[str] = None
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
    
    def select(self, *columns: str) -> "QueryBuilder":
        """Set columns to select."""
        self._select = list(columns)
        return self
    
    def where(self, condition: str, *params) -> "QueryBuilder":
        """Add WHERE condition."""
        self._where.append(condition)
        self._params.extend(params)
        return self
    
    def where_mood(self, mood: str) -> "QueryBuilder":
        """Filter by mood."""
        return self.where("mood = ?", mood)
    
    def where_energy_range(self, min_val: int, max_val: int) -> "QueryBuilder":
        """Filter by energy range."""
        return self.where("energy BETWEEN ? AND ?", min_val, max_val)
    
    def where_tempo_range(self, min_bpm: int, max_bpm: int) -> "QueryBuilder":
        """Filter by tempo range."""
        return self.where("tempo BETWEEN ? AND ?", min_bpm, max_bpm)
    
    def order_by(self, column: str, desc: bool = False) -> "QueryBuilder":
        """Set ORDER BY clause."""
        direction = "DESC" if desc else "ASC"
        self._order_by = f"{column} {direction}"
        return self
    
    def limit(self, n: int) -> "QueryBuilder":
        """Set LIMIT."""
        self._limit = n
        return self
    
    def offset(self, n: int) -> "QueryBuilder":
        """Set OFFSET."""
        self._offset = n
        return self
    
    def build(self) -> Tuple[str, tuple]:
        """Build the final query."""
        select_clause = ", ".join(self._select)
        query = f"SELECT {select_clause} FROM {self.table}"
        
        if self._where:
            query += " WHERE " + " AND ".join(self._where)
        
        if self._order_by:
            query += f" ORDER BY {self._order_by}"
        
        if self._limit:
            query += f" LIMIT {self._limit}"
        
        if self._offset:
            query += f" OFFSET {self._offset}"
        
        return query, tuple(self._params)
    
    def execute(self, pool: ConnectionPool) -> List[Dict]:
        """Execute the built query."""
        query, params = self.build()
        return pool.execute(query, params) or []


# ==================== CONVENIENCE FUNCTIONS ====================

def get_db_path() -> str:
    """Get default database path."""
    current_file = os.path.abspath(__file__)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    return os.path.join(backend_dir, "src", "database", "music.db")


def get_optimized_repo(db_path: str = None) -> OptimizedSongRepo:
    """Get optimized song repository."""
    if db_path is None:
        db_path = get_db_path()
    return OptimizedSongRepo(db_path)


def query(table: str = TABLE_SONGS) -> QueryBuilder:
    """Create a new query builder."""
    return QueryBuilder(table)
