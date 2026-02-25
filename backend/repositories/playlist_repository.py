"""
Playlist Repository
===================
Data access for playlists and playlist_songs tables.
"""

from typing import List, Dict, Optional
from datetime import datetime
from .base import BaseRepository


class PlaylistRepository(BaseRepository):
    """Repository for playlist operations."""
    
    TABLE = "playlists"
    PRIMARY_KEY = "playlist_id"
    
    def create(self, user_id: int, name: str, mood: str = None,
               description: str = None, is_auto_generated: bool = False) -> Optional[int]:
        """
        Create a new playlist.
        
        Returns:
            playlist_id if successful, None otherwise
        """
        with self.connection() as conn:
            cursor = conn.execute("""
                INSERT INTO playlists 
                (user_id, name, description, mood, is_auto_generated)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, name, description, mood, is_auto_generated))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_playlists(self, user_id: int, include_auto: bool = True) -> List[Dict]:
        """Get all playlists for a user."""
        with self.connection() as conn:
            if include_auto:
                cursor = conn.execute("""
                    SELECT * FROM playlists 
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                """, (user_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM playlists 
                    WHERE user_id = ? AND is_auto_generated = FALSE
                    ORDER BY updated_at DESC
                """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_playlist_with_songs(self, playlist_id: int) -> Optional[Dict]:
        """Get playlist with all its songs."""
        with self.connection() as conn:
            # Get playlist info
            cursor = conn.execute(
                "SELECT * FROM playlists WHERE playlist_id = ?",
                (playlist_id,)
            )
            playlist = cursor.fetchone()
            if not playlist:
                return None
            
            playlist_dict = dict(playlist)
            
            # Get songs (use song_name aliased as name for compatibility)
            cursor = conn.execute("""
                SELECT ps.position, ps.added_at,
                       s.song_id, s.song_name as name, s.artist, s.genre, s.mood,
                       s.energy, s.valence, s.tempo, s.camelot_key
                FROM playlist_songs ps
                JOIN songs s ON ps.song_id = s.song_id
                WHERE ps.playlist_id = ?
                ORDER BY ps.position
            """, (playlist_id,))
            
            playlist_dict['songs'] = [dict(row) for row in cursor.fetchall()]
            return playlist_dict
    
    def add_song(self, playlist_id: int, song_id: int, 
                 position: int = None) -> bool:
        """Add song to playlist at specified position."""
        with self.connection() as conn:
            # If no position specified, add at end
            if position is None:
                cursor = conn.execute("""
                    SELECT COALESCE(MAX(position), 0) + 1 as next_pos
                    FROM playlist_songs WHERE playlist_id = ?
                """, (playlist_id,))
                position = cursor.fetchone()['next_pos']
            
            conn.execute("""
                INSERT INTO playlist_songs (playlist_id, song_id, position)
                VALUES (?, ?, ?)
            """, (playlist_id, song_id, position))
            
            # Update playlist metadata
            conn.execute("""
                UPDATE playlists 
                SET song_count = song_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE playlist_id = ?
            """, (playlist_id,))
            
            conn.commit()
            return True
    
    def add_songs_bulk(self, playlist_id: int, song_ids: List[int]) -> int:
        """Add multiple songs to playlist in order."""
        with self.connection() as conn:
            # Get starting position
            cursor = conn.execute("""
                SELECT COALESCE(MAX(position), 0) as max_pos
                FROM playlist_songs WHERE playlist_id = ?
            """, (playlist_id,))
            start_pos = cursor.fetchone()['max_pos'] + 1
            
            # Insert all songs
            for i, song_id in enumerate(song_ids):
                conn.execute("""
                    INSERT INTO playlist_songs (playlist_id, song_id, position)
                    VALUES (?, ?, ?)
                """, (playlist_id, song_id, start_pos + i))
            
            # Update playlist metadata
            conn.execute("""
                UPDATE playlists 
                SET song_count = song_count + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE playlist_id = ?
            """, (len(song_ids), playlist_id))
            
            conn.commit()
            return len(song_ids)
    
    def remove_song(self, playlist_id: int, song_id: int) -> bool:
        """Remove song from playlist."""
        with self.connection() as conn:
            cursor = conn.execute("""
                DELETE FROM playlist_songs
                WHERE playlist_id = ? AND song_id = ?
            """, (playlist_id, song_id))
            
            if cursor.rowcount > 0:
                # Reorder remaining songs
                self._reorder_positions(conn, playlist_id)
                
                # Update count
                conn.execute("""
                    UPDATE playlists 
                    SET song_count = song_count - 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE playlist_id = ?
                """, (playlist_id,))
                conn.commit()
                return True
            return False
    
    def reorder_songs(self, playlist_id: int, song_order: List[int]) -> bool:
        """
        Reorder songs in playlist.
        
        Args:
            playlist_id: Playlist ID
            song_order: List of song_ids in new order
        """
        with self.connection() as conn:
            for i, song_id in enumerate(song_order):
                conn.execute("""
                    UPDATE playlist_songs
                    SET position = ?
                    WHERE playlist_id = ? AND song_id = ?
                """, (i + 1, playlist_id, song_id))
            
            conn.execute("""
                UPDATE playlists SET updated_at = CURRENT_TIMESTAMP
                WHERE playlist_id = ?
            """, (playlist_id,))
            
            conn.commit()
            return True
    
    def _reorder_positions(self, conn, playlist_id: int):
        """Reorder positions to be sequential."""
        cursor = conn.execute("""
            SELECT id, song_id FROM playlist_songs
            WHERE playlist_id = ?
            ORDER BY position
        """, (playlist_id,))
        
        for i, row in enumerate(cursor.fetchall()):
            conn.execute("""
                UPDATE playlist_songs SET position = ?
                WHERE id = ?
            """, (i + 1, row['id']))
    
    def update_playlist(self, playlist_id: int, **fields) -> bool:
        """Update playlist metadata."""
        allowed_fields = {'name', 'description', 'mood'}
        update_fields = {k: v for k, v in fields.items() if k in allowed_fields}
        
        if not update_fields:
            return False
        
        with self.connection() as conn:
            set_clause = ", ".join(f"{k} = ?" for k in update_fields)
            values = list(update_fields.values()) + [playlist_id]
            
            conn.execute(f"""
                UPDATE playlists 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE playlist_id = ?
            """, values)
            conn.commit()
            return True
    
    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete playlist and all its songs."""
        with self.connection() as conn:
            # Delete songs first (if no CASCADE)
            conn.execute(
                "DELETE FROM playlist_songs WHERE playlist_id = ?",
                (playlist_id,)
            )
            # Delete playlist
            cursor = conn.execute(
                "DELETE FROM playlists WHERE playlist_id = ?",
                (playlist_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def create_auto_playlist(self, user_id: int, mood: str, 
                             song_ids: List[int]) -> int:
        """
        Create auto-generated playlist from chat session.
        
        Returns:
            playlist_id
        """
        name = f"Playlist {mood} - {datetime.now().strftime('%d/%m %H:%M')}"
        playlist_id = self.create(
            user_id=user_id,
            name=name,
            mood=mood,
            description=f"Auto-generated for mood: {mood}",
            is_auto_generated=True
        )
        
        if playlist_id:
            self.add_songs_bulk(playlist_id, song_ids)
        
        return playlist_id
