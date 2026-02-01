"""Repository layer for user listening history operations."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sqlite3


TABLE_HISTORY = "listening_history"


def connect(db_path: str) -> sqlite3.Connection:
    """Create a database connection."""
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def ensure_history_table(con: sqlite3.Connection) -> None:
    """Create listening history table if it doesn't exist."""
    cur = con.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_HISTORY} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            song_id INTEGER NOT NULL,
            mood TEXT,
            rating INTEGER DEFAULT 0,
            liked INTEGER DEFAULT 0,
            play_count INTEGER DEFAULT 1,
            last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (song_id) REFERENCES songs(song_id)
        )
    """)
    # Create index for faster user queries
    cur.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_history_user 
        ON {TABLE_HISTORY}(user_id, last_played DESC)
    """)
    con.commit()


def add_history_entry(
    con: sqlite3.Connection,
    user_id: int,
    song_id: int,
    mood: Optional[str] = None,
    rating: int = 0,
    liked: bool = False
) -> int:
    """Add a new listening history entry. Returns the entry ID."""
    cur = con.cursor()
    
    # Check if entry exists for this user+song combination
    cur.execute(f"""
        SELECT id, play_count FROM {TABLE_HISTORY}
        WHERE user_id = ? AND song_id = ?
    """, (user_id, song_id))
    
    existing = cur.fetchone()
    
    if existing:
        # Update existing entry
        entry_id = existing['id']
        play_count = existing['play_count'] + 1
        cur.execute(f"""
            UPDATE {TABLE_HISTORY}
            SET play_count = ?,
                last_played = CURRENT_TIMESTAMP,
                mood = COALESCE(?, mood),
                rating = CASE WHEN ? > 0 THEN ? ELSE rating END,
                liked = CASE WHEN ? = 1 THEN 1 ELSE liked END
            WHERE id = ?
        """, (play_count, mood, rating, rating, int(liked), entry_id))
    else:
        # Insert new entry
        cur.execute(f"""
            INSERT INTO {TABLE_HISTORY}
            (user_id, song_id, mood, rating, liked)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, song_id, mood, rating, int(liked)))
        entry_id = cur.lastrowid
    
    con.commit()
    return entry_id


def get_user_history(
    con: sqlite3.Connection,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    mood_filter: Optional[str] = None
) -> List[Dict]:
    """Get listening history for a user."""
    cur = con.cursor()
    
    query = f"""
        SELECT h.*, s.song_name, s.artist_name, s.genre, s.energy, s.happiness, s.valence
        FROM {TABLE_HISTORY} h
        LEFT JOIN songs s ON h.song_id = s.song_id
        WHERE h.user_id = ?
    """
    params: List = [user_id]
    
    if mood_filter:
        query += " AND h.mood = ?"
        params.append(mood_filter)
    
    query += " ORDER BY h.last_played DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cur.execute(query, params)
    return [dict(row) for row in cur.fetchall()]


def get_liked_songs(con: sqlite3.Connection, user_id: int) -> List[Dict]:
    """Get all liked songs for a user."""
    cur = con.cursor()
    cur.execute(f"""
        SELECT h.*, s.song_name, s.artist_name, s.genre, s.energy, s.happiness, s.valence
        FROM {TABLE_HISTORY} h
        LEFT JOIN songs s ON h.song_id = s.song_id
        WHERE h.user_id = ? AND h.liked = 1
        ORDER BY h.last_played DESC
    """, (user_id,))
    return [dict(row) for row in cur.fetchall()]


def get_most_played(con: sqlite3.Connection, user_id: int, limit: int = 20) -> List[Dict]:
    """Get most played songs for a user."""
    cur = con.cursor()
    cur.execute(f"""
        SELECT h.*, s.song_name, s.artist_name, s.genre, s.energy, s.happiness, s.valence
        FROM {TABLE_HISTORY} h
        LEFT JOIN songs s ON h.song_id = s.song_id
        WHERE h.user_id = ?
        ORDER BY h.play_count DESC
        LIMIT ?
    """, (user_id, limit))
    return [dict(row) for row in cur.fetchall()]


def update_rating(con: sqlite3.Connection, user_id: int, song_id: int, rating: int) -> bool:
    """Update rating for a song in user's history. Rating should be 1-5."""
    if not 1 <= rating <= 5:
        return False
    
    cur = con.cursor()
    cur.execute(f"""
        UPDATE {TABLE_HISTORY}
        SET rating = ?
        WHERE user_id = ? AND song_id = ?
    """, (rating, user_id, song_id))
    con.commit()
    return cur.rowcount > 0


def update_like_status(con: sqlite3.Connection, user_id: int, song_id: int, liked: bool) -> bool:
    """Toggle like status for a song."""
    cur = con.cursor()
    cur.execute(f"""
        UPDATE {TABLE_HISTORY}
        SET liked = ?
        WHERE user_id = ? AND song_id = ?
    """, (int(liked), user_id, song_id))
    con.commit()
    return cur.rowcount > 0


def get_user_mood_stats(con: sqlite3.Connection, user_id: int) -> Dict[str, int]:
    """Get mood distribution from user's listening history."""
    cur = con.cursor()
    cur.execute(f"""
        SELECT mood, COUNT(*) as count
        FROM {TABLE_HISTORY}
        WHERE user_id = ? AND mood IS NOT NULL
        GROUP BY mood
        ORDER BY count DESC
    """, (user_id,))
    
    return {row['mood']: row['count'] for row in cur.fetchall()}


def get_user_preferences_data(con: sqlite3.Connection, user_id: int) -> Tuple[List[Dict], List[int]]:
    """Get songs and their like/rating status for preference model training.
    
    Returns:
        Tuple of (songs_list, labels) where labels are:
        - 1 for liked/highly rated songs
        - 0 for others
    """
    cur = con.cursor()
    cur.execute(f"""
        SELECT s.*, h.liked, h.rating
        FROM {TABLE_HISTORY} h
        JOIN songs s ON h.song_id = s.song_id
        WHERE h.user_id = ?
    """, (user_id,))
    
    songs = []
    labels = []
    
    for row in cur.fetchall():
        song_dict = dict(row)
        songs.append(song_dict)
        
        # Label as positive if liked or rating >= 4
        is_positive = song_dict.get('liked', 0) == 1 or song_dict.get('rating', 0) >= 4
        labels.append(1 if is_positive else 0)
    
    return songs, labels


def delete_history_entry(con: sqlite3.Connection, user_id: int, song_id: int) -> bool:
    """Delete a specific history entry."""
    cur = con.cursor()
    cur.execute(f"""
        DELETE FROM {TABLE_HISTORY}
        WHERE user_id = ? AND song_id = ?
    """, (user_id, song_id))
    con.commit()
    return cur.rowcount > 0


def clear_user_history(con: sqlite3.Connection, user_id: int) -> int:
    """Clear all history for a user. Returns number of deleted entries."""
    cur = con.cursor()
    cur.execute(f"""
        DELETE FROM {TABLE_HISTORY}
        WHERE user_id = ?
    """, (user_id,))
    con.commit()
    return cur.rowcount
