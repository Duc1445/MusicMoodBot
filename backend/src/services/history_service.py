"""Service layer for user listening history operations."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import sqlite3

from backend.src.repo import history_repo


class HistoryService:
    """Service class for managing user listening history."""
    
    def __init__(self, db_path: str):
        """Initialize with database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_table()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a new database connection."""
        return history_repo.connect(self.db_path)
    
    def _ensure_table(self) -> None:
        """Ensure the history table exists."""
        with self._get_connection() as con:
            history_repo.ensure_history_table(con)
    
    def record_play(
        self,
        user_id: int,
        song_id: int,
        mood: Optional[str] = None,
        rating: int = 0,
        liked: bool = False
    ) -> int:
        """Record a song play in user's history.
        
        Args:
            user_id: User identifier
            song_id: Song identifier
            mood: Current mood context (optional)
            rating: Song rating 1-5 (optional)
            liked: Whether user liked the song
            
        Returns:
            The history entry ID
        """
        with self._get_connection() as con:
            return history_repo.add_history_entry(
                con, user_id, song_id, mood, rating, liked
            )
    
    def get_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        mood_filter: Optional[str] = None
    ) -> List[Dict]:
        """Get user's listening history.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            offset: Pagination offset
            mood_filter: Optional mood to filter by
            
        Returns:
            List of history entries with song details
        """
        with self._get_connection() as con:
            return history_repo.get_user_history(
                con, user_id, limit, offset, mood_filter
            )
    
    def get_liked_songs(self, user_id: int) -> List[Dict]:
        """Get all songs the user has liked.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of liked songs with history details
        """
        with self._get_connection() as con:
            return history_repo.get_liked_songs(con, user_id)
    
    def get_top_songs(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's most played songs.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of most played songs
        """
        with self._get_connection() as con:
            return history_repo.get_most_played(con, user_id, limit)
    
    def rate_song(self, user_id: int, song_id: int, rating: int) -> bool:
        """Set rating for a song.
        
        Args:
            user_id: User identifier
            song_id: Song identifier
            rating: Rating value (1-5)
            
        Returns:
            True if rating was updated successfully
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        
        with self._get_connection() as con:
            return history_repo.update_rating(con, user_id, song_id, rating)
    
    def toggle_like(self, user_id: int, song_id: int, liked: bool) -> bool:
        """Set like status for a song.
        
        Args:
            user_id: User identifier
            song_id: Song identifier
            liked: Whether song should be liked
            
        Returns:
            True if status was updated successfully
        """
        with self._get_connection() as con:
            return history_repo.update_like_status(con, user_id, song_id, liked)
    
    def get_mood_statistics(self, user_id: int) -> Dict[str, int]:
        """Get mood distribution from user's history.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict mapping mood names to play counts
        """
        with self._get_connection() as con:
            return history_repo.get_user_mood_stats(con, user_id)
    
    def get_preference_training_data(self, user_id: int) -> Tuple[List[Dict], List[int]]:
        """Get data for training preference model.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (songs, labels) for model training
        """
        with self._get_connection() as con:
            return history_repo.get_user_preferences_data(con, user_id)
    
    def remove_from_history(self, user_id: int, song_id: int) -> bool:
        """Remove a song from user's history.
        
        Args:
            user_id: User identifier
            song_id: Song identifier
            
        Returns:
            True if entry was deleted
        """
        with self._get_connection() as con:
            return history_repo.delete_history_entry(con, user_id, song_id)
    
    def clear_history(self, user_id: int) -> int:
        """Clear all history for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of entries deleted
        """
        with self._get_connection() as con:
            return history_repo.clear_user_history(con, user_id)
    
    def get_recently_played(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recently played songs.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of recently played songs
        """
        return self.get_history(user_id, limit=limit)
    
    def has_listened_to(self, user_id: int, song_id: int) -> bool:
        """Check if user has listened to a song.
        
        Args:
            user_id: User identifier
            song_id: Song identifier
            
        Returns:
            True if song is in user's history
        """
        history = self.get_history(user_id, limit=1000)
        return any(h.get('song_id') == song_id for h in history)


def create_history_service(db_path: str) -> HistoryService:
    """Factory function to create HistoryService.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Configured HistoryService instance
    """
    return HistoryService(db_path)
