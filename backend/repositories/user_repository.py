"""
User Repository
===============
Data access for users table.
"""

from typing import Optional, Dict
from datetime import datetime
from .base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for user data operations"""
    
    TABLE = "users"
    PRIMARY_KEY = "user_id"
    
    def get_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.TABLE} WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.TABLE} WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_by_identifier(self, identifier: str) -> Optional[Dict]:
        """Get user by username OR email"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.TABLE} WHERE username = ? OR email = ?",
                (identifier, identifier)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add(self, username: str, email: str, password_hash: str) -> Optional[int]:
        """Create a new user"""
        try:
            with self.connection() as conn:
                cursor = conn.execute(
                    f"""INSERT INTO {self.TABLE} 
                    (username, email, password_hash) 
                    VALUES (?, ?, ?)""",
                    (username, email, password_hash)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception:
            return None
    
    def username_exists(self, username: str) -> bool:
        """Check if username is taken"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT 1 FROM {self.TABLE} WHERE username = ?",
                (username,)
            )
            return cursor.fetchone() is not None
    
    def email_exists(self, email: str) -> bool:
        """Check if email is taken"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT 1 FROM {self.TABLE} WHERE email = ?",
                (email,)
            )
            return cursor.fetchone() is not None
    
    def update_stats(self, user_id: int, songs_listened: int = None, 
                     favorite_mood: str = None, favorite_artist: str = None) -> bool:
        """Update user listening statistics"""
        fields = {}
        if songs_listened is not None:
            fields["total_songs_listened"] = songs_listened
        if favorite_mood is not None:
            fields["favorite_mood"] = favorite_mood
        if favorite_artist is not None:
            fields["favorite_artist"] = favorite_artist
        
        if not fields:
            return False
        
        return self.update(user_id, **fields)
    
    def increment_songs_listened(self, user_id: int) -> bool:
        """Increment the songs listened count"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"""UPDATE {self.TABLE} 
                SET total_songs_listened = total_songs_listened + 1 
                WHERE {self.PRIMARY_KEY} = ?""",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
