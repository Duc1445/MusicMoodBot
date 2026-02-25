"""
Database Schema Migration v2.0
==============================
Adds production-level tables for:
- feedback (like/dislike tracking)
- user_preferences (learned weights)
- playlists (saved playlists)
- playlist_songs (playlist items)

Run this migration to upgrade existing database.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "music.db")


def get_connection(db_path: Optional[str] = None):
    """Get database connection with WAL mode."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if table exists."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    """Check if column exists in table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [row['name'] for row in cursor.fetchall()]
    return column_name in columns


def migrate_v2():
    """
    Migration v2.0 - Add production tables.
    
    New tables:
    - feedback
    - user_preferences
    - playlists
    - playlist_songs
    
    Modified tables:
    - users (add avatar_url, favorite_genres)
    - songs (ensure all audio features exist)
    - listening_history (add session tracking fields)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("MusicMoodBot Database Migration v2.0")
    print("=" * 60)
    
    # ========================================
    # 1. Update users table
    # ========================================
    print("\n[1/6] Updating users table...")
    
    if not column_exists(conn, 'users', 'avatar_url'):
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        print("  + Added avatar_url column")
    
    if not column_exists(conn, 'users', 'favorite_genres'):
        cursor.execute("ALTER TABLE users ADD COLUMN favorite_genres TEXT")
        print("  + Added favorite_genres column (JSON)")
    
    # ========================================
    # 2. Update songs table
    # ========================================
    print("\n[2/6] Updating songs table...")
    
    song_columns = [
        ("energy", "REAL DEFAULT 50"),
        ("valence", "REAL DEFAULT 50"),
        ("tempo", "REAL DEFAULT 120"),
        ("loudness", "REAL DEFAULT -10"),
        ("danceability", "REAL DEFAULT 50"),
        ("acousticness", "REAL DEFAULT 50"),
        ("mood", "TEXT"),
        ("camelot_key", "TEXT"),
        ("duration_seconds", "INTEGER DEFAULT 180"),
    ]
    
    for col_name, col_def in song_columns:
        if not column_exists(conn, 'songs', col_name):
            cursor.execute(f"ALTER TABLE songs ADD COLUMN {col_name} {col_def}")
            print(f"  + Added {col_name} column")
    
    # ========================================
    # 3. Update listening_history table
    # ========================================
    print("\n[3/6] Updating listening_history table...")
    
    history_columns = [
        ("input_type", "TEXT CHECK(input_type IN ('text', 'chip'))"),
        ("input_text", "TEXT"),
        ("session_id", "TEXT"),
        ("listened_duration_seconds", "INTEGER DEFAULT 0"),
        ("completed", "BOOLEAN DEFAULT FALSE"),
    ]
    
    # Check if listening_history exists, if not create it
    if not table_exists(conn, 'listening_history'):
        cursor.execute("""
            CREATE TABLE listening_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                song_id INTEGER NOT NULL,
                mood_at_time TEXT,
                intensity TEXT,
                input_type TEXT CHECK(input_type IN ('text', 'chip')),
                input_text TEXT,
                session_id TEXT,
                listened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                listened_duration_seconds INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (song_id) REFERENCES songs(song_id)
            )
        """)
        print("  + Created listening_history table")
    else:
        for col_name, col_def in history_columns:
            if not column_exists(conn, 'listening_history', col_name):
                # SQLite doesn't support CHECK in ALTER TABLE, use simple type
                simple_def = col_def.split(' CHECK')[0]
                cursor.execute(f"ALTER TABLE listening_history ADD COLUMN {col_name} {simple_def}")
                print(f"  + Added {col_name} column")
    
    # ========================================
    # 4. Create feedback table
    # ========================================
    print("\n[4/6] Creating feedback table...")
    
    if not table_exists(conn, 'feedback'):
        cursor.execute("""
            CREATE TABLE feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                song_id INTEGER NOT NULL,
                history_id INTEGER,
                feedback_type TEXT CHECK(feedback_type IN ('like', 'dislike', 'skip')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (song_id) REFERENCES songs(song_id),
                FOREIGN KEY (history_id) REFERENCES listening_history(history_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_song ON feedback(song_id)")
        print("  + Created feedback table with indexes")
    else:
        print("  = feedback table already exists")
    
    # ========================================
    # 5. Create user_preferences table
    # ========================================
    print("\n[5/6] Creating user_preferences table...")
    
    if not table_exists(conn, 'user_preferences'):
        cursor.execute("""
            CREATE TABLE user_preferences (
                preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                preference_type TEXT CHECK(preference_type IN ('mood', 'genre', 'artist', 'tempo', 'energy')),
                preference_value TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                interaction_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, preference_type, preference_value)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_preferences_user ON user_preferences(user_id)")
        print("  + Created user_preferences table with indexes")
    else:
        print("  = user_preferences table already exists")
    
    # ========================================
    # 6. Create playlists & playlist_songs tables
    # ========================================
    print("\n[6/6] Creating playlists tables...")
    
    if not table_exists(conn, 'playlists'):
        cursor.execute("""
            CREATE TABLE playlists (
                playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                mood TEXT,
                total_duration_seconds INTEGER DEFAULT 0,
                song_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_auto_generated BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_playlists_user ON playlists(user_id)")
        print("  + Created playlists table with indexes")
    else:
        print("  = playlists table already exists")
    
    if not table_exists(conn, 'playlist_songs'):
        cursor.execute("""
            CREATE TABLE playlist_songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                song_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE,
                FOREIGN KEY (song_id) REFERENCES songs(song_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_playlist_songs_playlist ON playlist_songs(playlist_id)")
        print("  + Created playlist_songs table with indexes")
    else:
        print("  = playlist_songs table already exists")
    
    # ========================================
    # Commit and close
    # ========================================
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("Migration v2.0 completed successfully!")
    print("=" * 60)


def verify_schema():
    """Verify all tables exist and have correct structure."""
    conn = get_connection()
    
    required_tables = [
        'users', 'songs', 'listening_history', 'chat_history',
        'recommendations', 'feedback', 'user_preferences', 
        'playlists', 'playlist_songs'
    ]
    
    print("\nVerifying schema...")
    all_ok = True
    
    for table in required_tables:
        exists = table_exists(conn, table)
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")
        if not exists:
            all_ok = False
    
    conn.close()
    return all_ok


if __name__ == "__main__":
    migrate_v2()
    verify_schema()
