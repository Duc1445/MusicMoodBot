"""
Auto-calculate missing music attributes using mood engine algorithm
"""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')  # Fix encoding issues

from backend.src.pipelines.mood_engine import MoodEngine, EngineConfig
from backend.src.services.constants import Song, MOODS

def calculate_missing_attributes():
    """Calculate and update missing music attributes in database"""
    
    db_path = 'backend/src/database/music.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("[1/3] Loading all songs from database...")
    # Get ALL songs first for fitting the engine
    cursor.execute("""
        SELECT song_id, song_name, artist, genre, energy, happiness, 
               danceability, acousticness, tempo, loudness, 
               valence_score, arousal_score, mood, intensity
        FROM songs
    """)
    
    all_songs_data = cursor.fetchall()
    total_all = len(all_songs_data)
    print(f"  Found {total_all} total songs\n")
    
    # Convert to Song dicts
    all_songs = []
    for row in all_songs_data:
        song_id, song_name, artist, genre, energy, happiness, danceability, acousticness, tempo, loudness, valence_score, arousal_score, mood, intensity = row
        song = {
            'song_id': song_id,
            'song_name': song_name,
            'artist': artist,
            'genre': genre or '',
            'energy': energy or 50,
            'happiness': happiness or 50,
            'danceability': danceability or 50,
            'acousticness': acousticness or 50,
            'tempo': tempo or 100,
            'loudness': loudness or -10,
            'speechiness': 0,
            'instrumentalness': 0,
            'liveness': 0,
            'popularity': 50
        }
        all_songs.append(song)
    
    # Initialize and fit mood engine
    print("[2/3] Initializing and training Mood Engine...")
    config = EngineConfig()
    engine = MoodEngine(config)
    engine.fit(all_songs)
    print("  Engine trained successfully\n")
    
    # Now calculate predictions for all songs
    print("[3/3] Calculating missing attributes...")
    print("=" * 60)
    
    updates = []
    
    for idx, song in enumerate(all_songs, 1):
        
        try:
            # Calculate using mood engine predict
            prediction = engine.predict(song)
            
            valence = prediction['valence_score']
            arousal = prediction['arousal_score']
            detected_mood = prediction['mood']
            intensity_int = prediction['intensity']
            mood_confidence = prediction['mood_confidence']
            mood_score = prediction['mood_score']
            
            # Map intensity to string
            intensity_map = {1: "Nhẹ", 2: "Vừa", 3: "Mạnh"}
            intensity_str = intensity_map.get(intensity_int, "Vừa")
            
            updates.append({
                'song_id': song['song_id'],
                'song_name': song['song_name'],
                'valence_score': valence,
                'arousal_score': arousal,
                'mood': detected_mood,
                'intensity': intensity_int,
                'mood_score': mood_score,
                'mood_confidence': mood_confidence
            })
            
            print(f"[{idx}/{total_all}] {song['song_name']} - {song['artist']}")
            print(f"  Valence: {valence:.2f} | Arousal: {arousal:.2f}")
            print(f"  Mood: {detected_mood} | Intensity: {intensity_str}")
            print(f"  Confidence: {mood_confidence:.2%}\n")
            
        except Exception as e:
            print(f"❌ Error processing song {song_id}: {e}\n")
            continue
    
    # Update database
    print("=" * 60)
    print("💾 Updating database...")
    
    for update in updates:
        cursor.execute("""
            UPDATE songs 
            SET valence_score = ?, 
                arousal_score = ?, 
                mood = ?, 
                intensity = ?, 
                mood_score = ?,
                mood_confidence = ?
            WHERE song_id = ?
        """, (
            update['valence_score'],
            update['arousal_score'],
            update['mood'],
            update['intensity'],
            update['mood_score'],
            update['mood_confidence'],
            update['song_id']
        ))
    
    conn.commit()
    print(f"Successfully updated {len(updates)} songs!")
    
    # Verify
    cursor.execute("""
        SELECT COUNT(*) FROM songs 
        WHERE mood IS NOT NULL AND mood != ''
          AND valence_score IS NOT NULL
          AND arousal_score IS NOT NULL
    """)
    completed = cursor.fetchone()[0]
    print(f"✓ {completed}/{total_all} songs now have complete attributes\n")
    
    # Show sample
    cursor.execute("""
        SELECT song_name, artist, mood, intensity, valence_score, arousal_score, mood_confidence
        FROM songs 
        WHERE mood IS NOT NULL
        LIMIT 5
    """)
    
    print("Sample updated songs:")
    print("-" * 60)
    for row in cursor.fetchall():
        song_name, artist, mood, intensity, valence, arousal, confidence = row
        intensity_map = {1: "Nhẹ", 2: "Vừa", 3: "Mạnh"}
        print(f"{song_name} - {artist}")
        print(f"  Mood: {mood} | Intensity: {intensity_map.get(intensity, 'Unknown')}")
        print(f"  Valence: {valence:.2f} | Arousal: {arousal:.2f} | Confidence: {confidence:.2%}\n")
    
    conn.close()
    print("=" * 60)
    print("Done!\n")

if __name__ == "__main__":
    calculate_missing_attributes()
