"""
Playlist management service.
Supports creating, managing, and sharing playlists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import sqlite3
import json
import os
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class PlaylistSong:
    """A song in a playlist with position and metadata."""
    song_id: int
    position: int
    added_at: datetime = field(default_factory=datetime.now)
    added_by: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Playlist:
    """A playlist with songs and metadata."""
    playlist_id: str
    name: str
    description: str = ""
    user_id: Optional[str] = None
    songs: List[PlaylistSong] = field(default_factory=list)
    mood_filter: Optional[str] = None
    is_public: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    cover_image: Optional[str] = None
    
    @property
    def song_count(self) -> int:
        return len(self.songs)
    
    @property
    def duration_estimate_minutes(self) -> int:
        # Assume average song is 3.5 minutes
        return int(self.song_count * 3.5)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "playlist_id": self.playlist_id,
            "name": self.name,
            "description": self.description,
            "user_id": self.user_id,
            "song_count": self.song_count,
            "duration_estimate_minutes": self.duration_estimate_minutes,
            "mood_filter": self.mood_filter,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "cover_image": self.cover_image
        }


class PlaylistService:
    """
    Service for managing playlists.
    
    Features:
    - Create/update/delete playlists
    - Add/remove songs
    - Reorder songs
    - Auto-generate playlists based on mood
    - Smart playlist suggestions
    """
    
    def __init__(self, db_path: str = "music.db"):
        self.db_path = db_path
        self._ensure_tables()
    
    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def _ensure_tables(self) -> None:
        """Create playlist tables if they don't exist."""
        con = self._connect()
        cur = con.cursor()
        
        # Playlists table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                user_id TEXT,
                mood_filter TEXT,
                is_public INTEGER DEFAULT 0,
                tags TEXT DEFAULT '[]',
                cover_image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Playlist songs junction table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS playlist_songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id TEXT NOT NULL,
                song_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by TEXT,
                notes TEXT,
                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE,
                FOREIGN KEY (song_id) REFERENCES songs(song_id),
                UNIQUE (playlist_id, song_id)
            )
        """)
        
        # Playlist follows
        cur.execute("""
            CREATE TABLE IF NOT EXISTS playlist_follows (
                user_id TEXT NOT NULL,
                playlist_id TEXT NOT NULL,
                followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, playlist_id),
                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_playlist_user ON playlists(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_playlist_songs_playlist ON playlist_songs(playlist_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_playlist_public ON playlists(is_public)")
        
        con.commit()
        con.close()
        logger.info("Playlist tables initialized")
    
    # ==================== PLAYLIST CRUD ====================
    
    def create_playlist(
        self,
        name: str,
        user_id: Optional[str] = None,
        description: str = "",
        mood_filter: Optional[str] = None,
        is_public: bool = False,
        tags: List[str] = None
    ) -> Playlist:
        """Create a new playlist."""
        playlist_id = str(uuid.uuid4())
        now = datetime.now()
        
        con = self._connect()
        cur = con.cursor()
        
        cur.execute("""
            INSERT INTO playlists 
            (playlist_id, name, description, user_id, mood_filter, is_public, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            playlist_id, name, description, user_id, mood_filter,
            1 if is_public else 0, json.dumps(tags or []),
            now, now
        ))
        
        con.commit()
        con.close()
        
        playlist = Playlist(
            playlist_id=playlist_id,
            name=name,
            description=description,
            user_id=user_id,
            mood_filter=mood_filter,
            is_public=is_public,
            tags=tags or [],
            created_at=now,
            updated_at=now
        )
        
        logger.info(f"Created playlist: {name} ({playlist_id})")
        return playlist
    
    def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """Get a playlist by ID with songs."""
        con = self._connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("SELECT * FROM playlists WHERE playlist_id = ?", (playlist_id,))
        row = cur.fetchone()
        
        if not row:
            con.close()
            return None
        
        # Get songs
        cur.execute("""
            SELECT song_id, position, added_at, added_by, notes
            FROM playlist_songs
            WHERE playlist_id = ?
            ORDER BY position
        """, (playlist_id,))
        
        songs = [
            PlaylistSong(
                song_id=r["song_id"],
                position=r["position"],
                added_at=datetime.fromisoformat(r["added_at"]) if r["added_at"] else datetime.now(),
                added_by=r["added_by"],
                notes=r["notes"]
            )
            for r in cur.fetchall()
        ]
        
        con.close()
        
        return Playlist(
            playlist_id=row["playlist_id"],
            name=row["name"],
            description=row["description"] or "",
            user_id=row["user_id"],
            songs=songs,
            mood_filter=row["mood_filter"],
            is_public=bool(row["is_public"]),
            tags=json.loads(row["tags"] or "[]"),
            cover_image=row["cover_image"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now()
        )
    
    def update_playlist(
        self,
        playlist_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Update playlist metadata."""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if is_public is not None:
            updates.append("is_public = ?")
            params.append(1 if is_public else 0)
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags))
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(playlist_id)
        
        con = self._connect()
        cur = con.cursor()
        
        cur.execute(
            f"UPDATE playlists SET {', '.join(updates)} WHERE playlist_id = ?",
            params
        )
        
        success = cur.rowcount > 0
        con.commit()
        con.close()
        
        return success
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist."""
        con = self._connect()
        cur = con.cursor()
        
        cur.execute("DELETE FROM playlists WHERE playlist_id = ?", (playlist_id,))
        success = cur.rowcount > 0
        
        con.commit()
        con.close()
        
        return success
    
    def get_user_playlists(self, user_id: str) -> List[Playlist]:
        """Get all playlists for a user."""
        con = self._connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("""
            SELECT * FROM playlists 
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))
        
        playlists = []
        for row in cur.fetchall():
            playlist = Playlist(
                playlist_id=row["playlist_id"],
                name=row["name"],
                description=row["description"] or "",
                user_id=row["user_id"],
                mood_filter=row["mood_filter"],
                is_public=bool(row["is_public"]),
                tags=json.loads(row["tags"] or "[]"),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now()
            )
            
            # Get song count
            cur.execute(
                "SELECT COUNT(*) FROM playlist_songs WHERE playlist_id = ?",
                (row["playlist_id"],)
            )
            count = cur.fetchone()[0]
            playlist.songs = [PlaylistSong(0, i) for i in range(count)]  # Placeholder
            
            playlists.append(playlist)
        
        con.close()
        return playlists
    
    def get_public_playlists(self, limit: int = 20) -> List[Playlist]:
        """Get public playlists."""
        con = self._connect()
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        cur.execute("""
            SELECT p.*, 
                   (SELECT COUNT(*) FROM playlist_songs WHERE playlist_id = p.playlist_id) as song_count,
                   (SELECT COUNT(*) FROM playlist_follows WHERE playlist_id = p.playlist_id) as followers
            FROM playlists p
            WHERE is_public = 1
            ORDER BY followers DESC, updated_at DESC
            LIMIT ?
        """, (limit,))
        
        playlists = []
        for row in cur.fetchall():
            playlist = Playlist(
                playlist_id=row["playlist_id"],
                name=row["name"],
                description=row["description"] or "",
                user_id=row["user_id"],
                mood_filter=row["mood_filter"],
                is_public=True,
                tags=json.loads(row["tags"] or "[]"),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now()
            )
            # Set song count
            playlist.songs = [PlaylistSong(0, i) for i in range(row["song_count"])]
            playlists.append(playlist)
        
        con.close()
        return playlists
    
    # ==================== SONG MANAGEMENT ====================
    
    def add_song(
        self,
        playlist_id: str,
        song_id: int,
        added_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Add a song to a playlist."""
        con = self._connect()
        cur = con.cursor()
        
        # Get next position
        cur.execute(
            "SELECT COALESCE(MAX(position), 0) + 1 FROM playlist_songs WHERE playlist_id = ?",
            (playlist_id,)
        )
        position = cur.fetchone()[0]
        
        try:
            cur.execute("""
                INSERT INTO playlist_songs (playlist_id, song_id, position, added_by, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (playlist_id, song_id, position, added_by, notes))
            
            # Update playlist timestamp
            cur.execute(
                "UPDATE playlists SET updated_at = ? WHERE playlist_id = ?",
                (datetime.now(), playlist_id)
            )
            
            con.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        
        con.close()
        return success
    
    def add_songs_batch(
        self,
        playlist_id: str,
        song_ids: List[int],
        added_by: Optional[str] = None
    ) -> int:
        """Add multiple songs to a playlist."""
        con = self._connect()
        cur = con.cursor()
        
        # Get next position
        cur.execute(
            "SELECT COALESCE(MAX(position), 0) FROM playlist_songs WHERE playlist_id = ?",
            (playlist_id,)
        )
        position = cur.fetchone()[0]
        
        added = 0
        for song_id in song_ids:
            position += 1
            try:
                cur.execute("""
                    INSERT INTO playlist_songs (playlist_id, song_id, position, added_by)
                    VALUES (?, ?, ?, ?)
                """, (playlist_id, song_id, position, added_by))
                added += 1
            except sqlite3.IntegrityError:
                continue
        
        # Update playlist timestamp
        cur.execute(
            "UPDATE playlists SET updated_at = ? WHERE playlist_id = ?",
            (datetime.now(), playlist_id)
        )
        
        con.commit()
        con.close()
        return added
    
    def remove_song(self, playlist_id: str, song_id: int) -> bool:
        """Remove a song from a playlist."""
        con = self._connect()
        cur = con.cursor()
        
        cur.execute("""
            DELETE FROM playlist_songs 
            WHERE playlist_id = ? AND song_id = ?
        """, (playlist_id, song_id))
        
        success = cur.rowcount > 0
        
        if success:
            # Reorder positions
            cur.execute("""
                UPDATE playlist_songs 
                SET position = (
                    SELECT COUNT(*) 
                    FROM playlist_songs ps2 
                    WHERE ps2.playlist_id = playlist_songs.playlist_id 
                    AND ps2.position < playlist_songs.position
                ) + 1
                WHERE playlist_id = ?
            """, (playlist_id,))
            
            cur.execute(
                "UPDATE playlists SET updated_at = ? WHERE playlist_id = ?",
                (datetime.now(), playlist_id)
            )
        
        con.commit()
        con.close()
        return success
    
    def reorder_songs(self, playlist_id: str, song_id: int, new_position: int) -> bool:
        """Move a song to a new position in the playlist."""
        con = self._connect()
        cur = con.cursor()
        
        # Get current position
        cur.execute("""
            SELECT position FROM playlist_songs 
            WHERE playlist_id = ? AND song_id = ?
        """, (playlist_id, song_id))
        
        result = cur.fetchone()
        if not result:
            con.close()
            return False
        
        old_position = result[0]
        
        if old_position == new_position:
            con.close()
            return True
        
        # Shift other songs
        if new_position < old_position:
            cur.execute("""
                UPDATE playlist_songs 
                SET position = position + 1
                WHERE playlist_id = ? AND position >= ? AND position < ?
            """, (playlist_id, new_position, old_position))
        else:
            cur.execute("""
                UPDATE playlist_songs 
                SET position = position - 1
                WHERE playlist_id = ? AND position > ? AND position <= ?
            """, (playlist_id, old_position, new_position))
        
        # Update target song
        cur.execute("""
            UPDATE playlist_songs 
            SET position = ?
            WHERE playlist_id = ? AND song_id = ?
        """, (new_position, playlist_id, song_id))
        
        con.commit()
        con.close()
        return True
    
    # ==================== SMART PLAYLISTS ====================
    
    def create_mood_playlist(
        self,
        mood: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> Playlist:
        """Create a playlist automatically based on mood."""
        from backend.src.repo.song_repo import connect, fetch_songs
        
        # Get songs with matching mood
        con = connect(self.db_path)
        songs = fetch_songs(con, "mood = ?", (mood,))
        con.close()
        
        # Sort by mood_score
        songs = sorted(
            songs,
            key=lambda s: float(s.get("mood_score", 0) or 0),
            reverse=True
        )[:limit]
        
        # Create playlist
        from backend.src.services.constants import MOOD_EN_TO_VI, MOOD_EMOJI
        
        mood_vi = MOOD_EN_TO_VI.get(mood, mood)
        emoji = MOOD_EMOJI.get(mood, "🎵")
        
        playlist = self.create_playlist(
            name=f"{emoji} {mood_vi} Vibes",
            user_id=user_id,
            description=f"Playlist tự động tạo cho tâm trạng {mood_vi}",
            mood_filter=mood,
            tags=[mood, "auto-generated"]
        )
        
        # Add songs
        song_ids = [s["song_id"] for s in songs]
        self.add_songs_batch(playlist.playlist_id, song_ids)
        
        return playlist
    
    def create_mixed_mood_playlist(
        self,
        moods: List[str],
        user_id: Optional[str] = None,
        limit: int = 25
    ) -> Playlist:
        """Create a playlist mixing multiple moods."""
        from backend.src.repo.song_repo import connect, fetch_songs
        
        all_songs = []
        per_mood_limit = limit // len(moods) + 1
        
        con = connect(self.db_path)
        for mood in moods:
            songs = fetch_songs(con, "mood = ?", (mood,))
            songs = sorted(
                songs,
                key=lambda s: float(s.get("mood_score", 0) or 0),
                reverse=True
            )[:per_mood_limit]
            all_songs.extend(songs)
        con.close()
        
        # Shuffle and limit
        import random
        random.shuffle(all_songs)
        all_songs = all_songs[:limit]
        
        # Create playlist
        mood_names = ", ".join(moods)
        playlist = self.create_playlist(
            name=f"🎭 Mixed: {mood_names}",
            user_id=user_id,
            description=f"Playlist pha trộn các tâm trạng: {mood_names}",
            tags=moods + ["mixed", "auto-generated"]
        )
        
        song_ids = [s["song_id"] for s in all_songs]
        self.add_songs_batch(playlist.playlist_id, song_ids)
        
        return playlist
    
    def get_playlist_with_songs(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Get playlist with full song details."""
        playlist = self.get_playlist(playlist_id)
        if not playlist:
            return None
        
        from backend.src.repo.song_repo import connect, fetch_song_by_id
        
        con = connect(self.db_path)
        songs_with_details = []
        
        for ps in playlist.songs:
            song = fetch_song_by_id(con, ps.song_id)
            if song:
                song["position"] = ps.position
                song["added_at"] = ps.added_at.isoformat()
                songs_with_details.append(song)
        
        con.close()
        
        result = playlist.to_dict()
        result["songs"] = songs_with_details
        return result


# Global instance
_playlist_service: Optional[PlaylistService] = None


def get_playlist_service(db_path: str = None) -> PlaylistService:
    """Get or create playlist service instance."""
    global _playlist_service
    if _playlist_service is None:
        if db_path is None:
            current_file = os.path.abspath(__file__)
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            db_path = os.path.join(backend_dir, "src", "database", "music.db")
        _playlist_service = PlaylistService(db_path)
    return _playlist_service
