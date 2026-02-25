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
from .feedback_repository import FeedbackRepository
from .preferences_repository import UserPreferencesRepository
from .playlist_repository import PlaylistRepository

# Connection pool for shared access
from .connection import get_connection, get_db_path

__all__ = [
    "BaseRepository",
    "SongRepository", 
    "UserRepository",
    "HistoryRepository",
    "FeedbackRepository",
    "UserPreferencesRepository",
    "PlaylistRepository",
    "get_connection",
    "get_db_path",
]
