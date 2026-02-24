"""
Simple Demo to show music data from new music.db with mood predictions
"""
import sqlite3
from typing import List, Dict

def get_songs_from_db() -> List[Dict]:
    """Get all songs from the database"""
    db_path = 'backend/src/database/music.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT song_id, song_name, artist, genre, mood, intensity,
               valence_score, arousal_score, mood_confidence, mood_score
        FROM songs
        ORDER BY mood, song_name
    """)
    
    songs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return songs

def get_api_songs() -> List[Dict]:
    """Get songs from API"""
    # Skip API call for now
    return None

def format_mood_emoji(mood: str) -> str:
    """Get emoji for mood"""
    emojis = {
        'happy': '😊',
        'sad': '😢',
        'energetic': '⚡',
        'stress': '🧠',
        'angry': '😠'
    }
    return emojis.get(mood, '🎵')

def format_intensity_emoji(intensity: int) -> str:
    """Get emoji for intensity"""
    intensity_map = {
        1: '🌿 Nhẹ',
        2: '✨ Vừa',
        3: '🔥 Mạnh'
    }
    return intensity_map.get(intensity, '?')

def print_demo():
    """Print demo with new music database"""
    print("\n" + "="*80)
    print("🎵 MUSIC MOOD PREDICTION - DEMO WITH NEW MUSIC DATABASE 🎵".center(80))
    print("="*80)
    
    # Get songs
    songs = get_songs_from_db()
    
    if not songs:
        print("❌ No songs found in database")
        return
    
    print(f"\n✅ Loaded {len(songs)} songs from database\n")
    
    # Group by mood
    moods_dict = {}
    for song in songs:
        mood = song['mood'] or 'Unknown'
        if mood not in moods_dict:
            moods_dict[mood] = []
        moods_dict[mood].append(song)
    
    # Display by mood
    for mood, mood_songs in sorted(moods_dict.items()):
        emoji = format_mood_emoji(mood)
        print(f"\n{emoji} {mood.upper()} - {len(mood_songs)} songs")
        print("-" * 80)
        
        for i, song in enumerate(mood_songs[:5], 1):  # Show first 5 of each mood
            intensity = format_intensity_emoji(song['intensity'])
            confidence = f"{song['mood_confidence']*100:.1f}%" if song['mood_confidence'] else "N/A"
            valence = f"{song['valence_score']:.1f}" if song['valence_score'] else "N/A"
            arousal = f"{song['arousal_score']:.1f}" if song['arousal_score'] else "N/A"
            
            print(f"\n  {i}. {song['song_name']}")
            print(f"     🎤 Artist: {song['artist']}")
            print(f"     🎼 Genre: {song['genre']}")
            print(f"     {intensity}")
            print(f"     Valence: {valence} | Arousal: {arousal} | Confidence: {confidence}")
        
        if len(mood_songs) > 5:
            print(f"\n  ... and {len(mood_songs) - 5} more songs")
    
    # Summary stats
    print("\n" + "="*80)
    print("📊 SUMMARY STATISTICS".center(80))
    print("="*80)
    
    total_songs = len(songs)
    avg_confidence = sum(s['mood_confidence'] for s in songs if s['mood_confidence']) / total_songs if songs else 0
    avg_valence = sum(s['valence_score'] for s in songs if s['valence_score']) / total_songs if songs else 0
    avg_arousal = sum(s['arousal_score'] for s in songs if s['arousal_score']) / total_songs if songs else 0
    
    print(f"\nTotal songs: {total_songs}")
    print(f"Average mood confidence: {avg_confidence*100:.1f}%")
    print(f"Average valence score: {avg_valence:.1f}")
    print(f"Average arousal score: {avg_arousal:.1f}")
    
    print("\nMood distribution:")
    for mood, mood_songs in sorted(moods_dict.items()):
        percentage = (len(mood_songs) / total_songs) * 100
        bar = "█" * int(percentage / 5)
        print(f"  {mood:12s} {bar:20s} {len(mood_songs):2d} ({percentage:5.1f}%)")
    
    print("\n" + "="*80)
    print("🚀 NEXT STEPS:".center(80))
    print("="*80)
    print("""
  1. View API Documentation: http://localhost:8000/api/docs
  2. Try API Endpoints:
     - GET /api/songs - List all songs with mood data
     - POST /api/search - Search by mood/text
     - GET /api/recommendations - Get personalized recommendations
     - POST /api/analyze - Analyze song text/mood
  
  3. Use the Frontend UI to:
     - Browse songs by mood
     - Get mood-based recommendations
     - Chat with the music mood bot
     - Analyze your listening preferences
    """)
    print("="*80)

if __name__ == "__main__":
    print_demo()
