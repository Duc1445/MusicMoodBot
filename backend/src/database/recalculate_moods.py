"""Recalculate mood predictions with Engine v4.0"""
import sqlite3
import os

# Add parent to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from backend.src.pipelines.mood_engine import MoodEngine

DB_PATH = os.path.join(os.path.dirname(__file__), "music.db")

def recalculate_moods():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute('SELECT * FROM songs')
    songs = [dict(row) for row in cur.fetchall()]

    print('=' * 60)
    print('🎵 Recalculating mood predictions with Engine v4.0')
    print('=' * 60)

    engine = MoodEngine()
    engine.fit(songs)

    print(f'\n🔄 Processing {len(songs)} songs...\n')

    mood_emoji = {'energetic': '⚡', 'happy': '😊', 'sad': '😢', 'stress': '😰', 'angry': '😠'}
    int_label = {1: 'Nhẹ', 2: 'Vừa', 3: 'Mạnh'}

    for i, song in enumerate(songs, 1):
        result = engine.predict(song)
        
        cur.execute('''
            UPDATE songs SET
                mood = ?,
                intensity = ?,
                mood_score = ?,
                valence_score = ?,
                arousal_score = ?,
                mood_confidence = ?
            WHERE song_id = ?
        ''', (
            result['mood'],
            result['intensity'],
            round(result['mood_score'], 2),
            round(result['valence_score'], 2),
            round(result['arousal_score'], 2),
            round(result['mood_confidence'], 4),
            song['song_id']
        ))
        
        print(f"[{i}/{len(songs)}] {song['song_name']} - {song['artist']}")
        print(f"   {mood_emoji.get(result['mood'], '')} {result['mood']} | Intensity: {int_label[result['intensity']]}")
        print(f"   Valence: {result['valence_score']:.1f} | Arousal: {result['arousal_score']:.1f} | Conf: {result['mood_confidence']*100:.1f}%")

    con.commit()

    print('\n' + '=' * 60)
    print('📊 MOOD DISTRIBUTION')
    print('=' * 60)
    cur.execute('SELECT mood, COUNT(*) FROM songs GROUP BY mood')
    for mood, count in cur.fetchall():
        emoji = mood_emoji.get(mood, '')
        print(f'   {emoji} {mood}: {count} songs')

    cur.execute('SELECT AVG(mood_confidence) FROM songs')
    avg_conf = cur.fetchone()[0]
    print(f'\n📈 Average Confidence: {avg_conf*100:.1f}%')

    con.close()
    print('\n✅ Done!')

if __name__ == "__main__":
    recalculate_moods()
