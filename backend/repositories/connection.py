"""
Database Connection Utilities
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional

# Default database path
_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__), 
    "..", "src", "database", "music.db"
)

def get_db_path() -> str:
    """Get the database file path"""
    return os.environ.get("MMB_DB_PATH", _DEFAULT_DB_PATH)


@contextmanager
def get_connection(db_path: Optional[str] = None):
    """
    Context manager for database connections.
    
    Usage:
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM songs")
            rows = cursor.fetchall()
    """
    path = db_path or get_db_path()
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()
