"""
Base Repository
===============
Abstract base class for all repositories.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any
from contextlib import contextmanager
import sqlite3

from .connection import get_connection, get_db_path

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Base repository with common CRUD operations.
    
    Subclasses must define:
        - TABLE: str - table name
        - PRIMARY_KEY: str - primary key column name
    """
    
    TABLE: str = ""
    PRIMARY_KEY: str = "id"
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
    
    @contextmanager
    def connection(self):
        """Get a database connection context"""
        with get_connection(self.db_path) as conn:
            yield conn
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all records with pagination"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.TABLE} LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_id(self, record_id: Any) -> Optional[Dict]:
        """Get a single record by primary key"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.TABLE} WHERE {self.PRIMARY_KEY} = ?",
                (record_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def count(self) -> int:
        """Count all records"""
        with self.connection() as conn:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {self.TABLE}")
            return cursor.fetchone()[0]
    
    def exists(self, record_id: Any) -> bool:
        """Check if record exists"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT 1 FROM {self.TABLE} WHERE {self.PRIMARY_KEY} = ?",
                (record_id,)
            )
            return cursor.fetchone() is not None
    
    def delete(self, record_id: Any) -> bool:
        """Delete a record by primary key"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM {self.TABLE} WHERE {self.PRIMARY_KEY} = ?",
                (record_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def update(self, record_id: Any, **fields) -> bool:
        """Update a record with given fields"""
        if not fields:
            return False
        
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [record_id]
        
        with self.connection() as conn:
            cursor = conn.execute(
                f"UPDATE {self.TABLE} SET {set_clause} WHERE {self.PRIMARY_KEY} = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0
