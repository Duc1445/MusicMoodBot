#!/usr/bin/env python
"""
Helper script to bulk insert/update songs in database.
Usage: Update the SONGS list below and run this script.
"""

import sqlite3
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "music.db")

# Format: (song_name, artist, genre, happiness, danceability, energy, loudness, tempo, acousticness, source)
SONGS_TO_UPDATE = [
    # Example - Update these with TuneBat data
    # ("Lạc Trôi", "Sơn Tùng MTP", "Pop", 17, 64, 87, -4, 135, 33, "tunebat"),
]

def update_songs_batch(songs_data):
    """Update songs with audio features from TuneBat."""
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    
    updated = 0
    for song_name, artist, genre, happiness, danceability, energy, loudness, tempo, acousticness, source in songs_data:
        try:
            cursor.execute("""
                UPDATE songs SET
                    happiness = ?,
                    danceability = ?,
                    energy = ?,
                    loudness = ?,
                    tempo = ?,
                    acousticness = ?,
                    source = ?
                WHERE song_name = ? AND artist = ?
            """, (happiness, danceability, energy, loudness, tempo, acousticness, source, song_name, artist))
            
            if cursor.rowcount > 0:
                print(f"✓ Updated: {song_name} - {artist}")
                updated += 1
            else:
                print(f"✗ Not found: {song_name} - {artist}")
        except Exception as e:
            print(f"✗ Error updating {song_name}: {e}")
    
    con.commit()
    con.close()
    
    print(f"\n✓ Updated {updated} songs")

def run_mood_predictions():
    """Run mood prediction algorithm on all songs."""
    import sys
    sys.path.insert(0, backend_dir)
    
    from backend.src.services.mood_services import DBMoodEngine
    
    print("\nRunning mood predictions...")
    engine = DBMoodEngine(db_path=db_path, add_debug_cols=True)
    engine.fit(force=True)
    count = engine.update_all()
    print(f"✓ Computed mood for {count} songs")

if __name__ == "__main__":
    if SONGS_TO_UPDATE:
        update_songs_batch(SONGS_TO_UPDATE)
        run_mood_predictions()
    else:
        print("No songs to update. Edit SONGS_TO_UPDATE list and run again.")
        print("\nCurrent songs in database:")
        con = sqlite3.connect(db_path)
        cursor = con.cursor()
        cursor.execute("SELECT song_id, song_name, artist FROM songs ORDER BY song_id")
        for row in cursor.fetchall():
            print(f"  {row[0]:2d}. {row[1]:30s} - {row[2]}")
        con.close()
