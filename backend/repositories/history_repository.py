"""
History Repository
==================
Data access for chat_history and recommendations tables.
"""

from typing import List, Dict, Optional
from datetime import datetime
from .base import BaseRepository


class HistoryRepository(BaseRepository):
    """Repository for chat history and recommendations"""
    
    TABLE = "chat_history"
    PRIMARY_KEY = "history_id"
    
    def add_chat_entry(self, user_id: int, mood: str = None, 
                       intensity: str = None, song_id: int = None, 
                       reason: str = None) -> Optional[int]:
        """Add a chat history entry"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"""INSERT INTO {self.TABLE} 
                (user_id, mood, intensity, song_id, reason) 
                VALUES (?, ?, ?, ?, ?)""",
                (user_id, mood, intensity, song_id, reason)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_user_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get chat history for a user"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"""SELECT * FROM {self.TABLE} 
                WHERE user_id = ? 
                ORDER BY timestamp DESC LIMIT ?""",
                (user_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_mood_stats(self, user_id: int) -> Dict[str, int]:
        """Get mood frequency statistics for a user"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"""SELECT mood, COUNT(*) as count 
                FROM {self.TABLE} 
                WHERE user_id = ? AND mood IS NOT NULL 
                GROUP BY mood 
                ORDER BY count DESC""",
                (user_id,)
            )
            return {row["mood"]: row["count"] for row in cursor.fetchall()}
    
    # Recommendations table operations
    def add_recommendation(self, user_id: int, song_id: int, 
                           mood: str, intensity: str) -> Optional[int]:
        """Add a recommendation entry"""
        with self.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO recommendations 
                (user_id, song_id, mood, intensity) 
                VALUES (?, ?, ?, ?)""",
                (user_id, song_id, mood, intensity)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_user_recommendations(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get recommendations with song details for a user"""
        with self.connection() as conn:
            cursor = conn.execute(
                """SELECT r.*, s.name as song_name, s.artist, s.genre, s.mood as song_mood
                FROM recommendations r 
                LEFT JOIN songs s ON r.song_id = s.song_id 
                WHERE r.user_id = ? 
                ORDER BY r.timestamp DESC 
                LIMIT ?""",
                (user_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_songs(self, user_id: int, limit: int = 10) -> List[int]:
        """Get recently recommended song IDs for a user"""
        with self.connection() as conn:
            cursor = conn.execute(
                """SELECT DISTINCT song_id FROM recommendations 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?""",
                (user_id, limit)
            )
            return [row["song_id"] for row in cursor.fetchall()]
    
    def clear_user_history(self, user_id: int) -> int:
        """Clear all history for a user, returns deleted count"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM {self.TABLE} WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount
