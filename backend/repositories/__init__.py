"""
Repositories Package
====================
Data access layer with Repository Pattern.

Each repository handles CRUD operations for one entity type.
Uses context managers for safe database connections.
"""

from .base import BaseRepository
from .song_repository import SongRepository
from .user_repository import UserRepository
from .history_repository import HistoryRepository

# Connection pool for shared access
from .connection import get_connection, get_db_path

__all__ = [
    "BaseRepository",
    "SongRepository", 
    "UserRepository",
    "HistoryRepository",
    "get_connection",
    "get_db_path",
]
