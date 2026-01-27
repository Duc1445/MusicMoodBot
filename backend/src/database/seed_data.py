"""Seed database with sample song data for testing and development."""

import sqlite3
import os
from typing import Optional


def seed_songs(
    db_path: Optional[str] = None,
    clear_existing: bool = False
) -> int:
    """
    Seed database with sample songs.
    
    Args:
        db_path: Path to database file. If None, uses backend/music.db
        clear_existing: Whether to clear existing songs before seeding
    """
    if db_path is None:
        # Use absolute path from backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(backend_dir, "music.db")
    """
    Seed database with sample songs for testing.
    
    Args:
        db_path: Path to SQLite database file
        clear_existing: If True, delete existing songs before seeding
        
    Returns:
        Number of songs inserted
    """
    sample_songs = [
        # (title, artist, genre, energy, valence, tempo, loudness, danceability, acousticness)
        ("Levitating", "Dua Lipa", "pop", 85, 88, 103.5, -4.1, 82, 8),
        ("Blinding Lights", "The Weeknd", "synthwave+pop", 73, 52, 103.9, -5.9, 80, 0),
        ("Good as Hell", "Lizzo", "pop+hip-hop", 88, 90, 160.0, -7.3, 72, 6),
        ("Shape of You", "Ed Sheeran", "pop", 82, 72, 96.0, -3.3, 80, 10),
        ("Someone Like You", "Adele", "pop+ballad", 30, 35, 67.9, -6.1, 45, 88),
        ("Paparazzi", "Lady Gaga", "pop+dance", 92, 75, 120.0, -3.8, 85, 3),
        ("Smells Like Teen Spirit", "Nirvana", "rock+grunge", 92, 40, 119.9, -3.0, 52, 18),
        ("Hotel California", "Eagles", "rock+ballad", 40, 38, 175.0, -11.8, 50, 75),
        ("Bohemian Rhapsody", "Queen", "rock+opera", 75, 68, 145.0, -7.1, 48, 35),
        ("Imagine", "John Lennon", "rock+ballad", 32, 70, 92.0, -14.2, 42, 91),
        ("Uptown Funk", "Mark Ronson ft. Bruno Mars", "funk+pop", 95, 82, 104.0, -5.2, 90, 5),
        ("Dark Side of the Moon", "Pink Floyd", "rock+progressive", 50, 45, 120.0, -9.0, 40, 42),
        ("Lose Yourself", "Eminem", "hip-hop", 90, 40, 171.0, -5.5, 78, 18),
        ("All the Stars", "Kendrick Lamar & SZA", "hip-hop+r&b", 65, 55, 100.0, -7.8, 68, 22),
        ("Energy", "Drake", "hip-hop+pop", 88, 60, 104.0, -4.2, 75, 15),
        ("Sad", "XXXTentacion", "hip-hop+emo", 35, 25, 140.0, -8.5, 55, 45),
        ("Stressed", "Logic ft. Alessia Cara", "hip-hop+pop", 65, 35, 152.0, -4.1, 72, 25),
        ("Angry Birds Theme", "PNAU", "electronic+pop", 98, 45, 128.0, -3.0, 88, 8),
        ("Chill Out", "Air", "electronic+chillwave", 25, 65, 100.0, -10.0, 40, 65),
        ("Synthesize", "Daft Punk", "electronic+dance", 92, 75, 120.0, -4.5, 85, 12),
    ]
    
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        
        # Clear existing songs if requested
        if clear_existing:
            cur.execute("DELETE FROM songs")
            con.commit()
            print("[INFO] Cleared existing songs")
        
        # Insert sample songs
        for title, artist, genre, energy, valence, tempo, loudness, danceability, acousticness in sample_songs:
            cur.execute("""
                INSERT OR IGNORE INTO songs 
                (song_name, artist, genre, energy, happiness, tempo, loudness, danceability, acousticness)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, artist, genre, energy, valence, tempo, loudness, danceability, acousticness))
        
        con.commit()
        print(f"[OK] Seeded {len(sample_songs)} sample songs")
        return len(sample_songs)
        
    except sqlite3.OperationalError as e:
        print(f"[ERROR] Database operation failed: {e}")
        print("[INFO] Run init_db.py first to create the database schema")
        raise
    except Exception as e:
        print(f"[ERROR] Failed to seed database: {e}")
        raise
    finally:
        con.close()


if __name__ == "__main__":
    seed_songs("music.db")


# ----------------------------
# Chạy CLI
#  import backend
# python -m backend.src.database.seed_data

# # Hoặc import như module
#
# from backend.src.database.seed_data import seed_songs
# seed_songs("music.db", clear_existing=True)
# ----------------------------