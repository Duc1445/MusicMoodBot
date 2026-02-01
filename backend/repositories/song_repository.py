"""
Song Repository
===============
Data access for songs table.
"""

from typing import List, Dict, Optional
from .base import BaseRepository


class SongRepository(BaseRepository):
    """Repository for song data operations"""
    
    TABLE = "songs"
    PRIMARY_KEY = "song_id"
    
    def get_by_mood(self, mood: str, limit: int = 20) -> List[Dict]:
        """Get songs filtered by mood"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.TABLE} WHERE mood = ? OR moods LIKE ? LIMIT ?",
                (mood, f"%{mood}%", limit)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_artist(self, artist: str, limit: int = 20) -> List[Dict]:
        """Get songs by artist (partial match)"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.TABLE} WHERE artist LIKE ? LIMIT ?",
                (f"%{artist}%", limit)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_genre(self, genre: str, limit: int = 20) -> List[Dict]:
        """Get songs by genre"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.TABLE} WHERE genre LIKE ? LIMIT ?",
                (f"%{genre}%", limit)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """Search songs by name, artist, or genre"""
        pattern = f"%{query}%"
        with self.connection() as conn:
            cursor = conn.execute(
                f"""SELECT * FROM {self.TABLE} 
                WHERE name LIKE ? OR song_name LIKE ? OR artist LIKE ? OR genre LIKE ? 
                LIMIT ?""",
                (pattern, pattern, pattern, pattern, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def add(self, name: str, artist: str, genre: str = None, 
            suy_score: float = None, reason: str = None, moods: str = None) -> Optional[int]:
        """Add a new song"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"""INSERT INTO {self.TABLE} 
                (name, artist, genre, suy_score, reason, moods) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, artist, genre, suy_score, reason, moods)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_random(self, limit: int = 5, mood: str = None) -> List[Dict]:
        """Get random songs, optionally filtered by mood"""
        with self.connection() as conn:
            if mood:
                cursor = conn.execute(
                    f"""SELECT * FROM {self.TABLE} 
                    WHERE mood = ? OR moods LIKE ? 
                    ORDER BY RANDOM() LIMIT ?""",
                    (mood, f"%{mood}%", limit)
                )
            else:
                cursor = conn.execute(
                    f"SELECT * FROM {self.TABLE} ORDER BY RANDOM() LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_top_rated(self, limit: int = 10) -> List[Dict]:
        """Get top rated songs by suy_score"""
        with self.connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.TABLE} ORDER BY suy_score DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
