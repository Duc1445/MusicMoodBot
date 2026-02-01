"""
Nâng cấp database music.db với các trọng số mới để prediction chính xác hơn.

Các thuộc tính mới được thêm:
1. speechiness      - Mức độ giọng nói (0-100): Cao = nhiều lời, Thấp = nhạc thuần
2. instrumentalness - Mức độ nhạc cụ (0-100): Cao = ít lời, Thấp = nhiều lời
3. liveness         - Mức độ live (0-100): Cao = thu live, Thấp = studio
4. popularity       - Độ phổ biến (0-100)
5. duration_ms      - Thời lượng bài hát (ms)
6. key              - Tông nhạc (0-11: C, C#, D, ...)
7. mode             - Điệu (0=minor, 1=major)
8. time_signature   - Nhịp (3, 4, 5, ...)
9. emotional_depth  - Chiều sâu cảm xúc (0-100) - TÍNH TOÁN TỪ CÁC THUỘC TÍNH
10. mood_stability  - Độ ổn định tâm trạng (0-100) - TÍNH TOÁN TỪ CÁC THUỘC TÍNH

Phiên bản: 3.1.0
"""

import sqlite3
import random
import math
from pathlib import Path

DB_PATH = Path(__file__).parent / "music.db"

# Dữ liệu ước lượng cho các bài hát Việt Nam phổ biến
# Dựa trên phân tích audio và đặc điểm nhạc Việt
SONG_ATTRIBUTES_ESTIMATES = {
    # song_id: (speechiness, instrumentalness, liveness, popularity, duration_ms, key, mode, time_signature)
    # Lạc Trôi - Sơn Tùng: Ballad rock, nhiều lời
    1: (8, 2, 12, 95, 259000, 7, 1, 4),  # G major
    # Có Chắc Yêu Là Đây - Sơn Tùng: Dance pop
    2: (6, 5, 8, 92, 204000, 5, 1, 4),   # F major
    # Nơi Này Có Anh - Sơn Tùng: Ballad
    3: (5, 8, 6, 90, 268000, 0, 1, 4),   # C major
    # Chúng Ta Của Hiện Tại - Sơn Tùng: Pop ballad
    4: (7, 3, 10, 88, 285000, 2, 0, 4),  # D minor
    # Hãy Trao Cho Anh - Sơn Tùng ft Snoop: Hip hop
    5: (15, 1, 8, 93, 254000, 9, 0, 4),  # A minor
    # Em Của Ngày Hôm Qua - Sơn Tùng: Pop rock
    6: (6, 4, 10, 85, 241000, 4, 1, 4),  # E major
    # Anh Sai Rồi - Sơn Tùng: Ballad
    7: (4, 12, 5, 78, 295000, 7, 0, 4),  # G minor
    # Muộn Rồi Mà Sao Còn - Sơn Tùng: R&B
    8: (8, 6, 7, 91, 312000, 1, 0, 4),   # C# minor
    # Chạy Ngay Đi - Sơn Tùng: EDM Pop
    9: (10, 3, 15, 89, 237000, 6, 1, 4), # F# major
    # Making My Way - Sơn Tùng: Pop
    10: (5, 7, 6, 87, 198000, 10, 1, 4), # A# major
    
    # Bích Phương songs
    11: (7, 5, 8, 82, 245000, 3, 1, 4),
    12: (6, 8, 6, 80, 262000, 8, 1, 4),
    
    # Hoàng Thùy Linh songs  
    13: (9, 4, 12, 85, 228000, 5, 1, 4),
    14: (8, 6, 10, 83, 241000, 0, 1, 4),
    
    # Jack songs
    15: (6, 5, 8, 88, 256000, 2, 1, 4),
    16: (5, 7, 6, 86, 278000, 7, 0, 4),
    
    # Đen Vâu songs (rap - cao speechiness)
    17: (25, 2, 15, 90, 315000, 4, 0, 4),
    18: (22, 3, 12, 88, 298000, 9, 0, 4),
    
    # Binz songs (rap)
    19: (20, 4, 10, 82, 245000, 1, 0, 4),
    20: (18, 5, 8, 80, 232000, 6, 0, 4),
    
    # Hà Anh Tuấn songs (ballad - cao acousticness)
    21: (4, 15, 5, 75, 320000, 3, 1, 4),
    22: (3, 18, 4, 72, 345000, 8, 1, 4),
    
    # Mỹ Tâm songs
    23: (5, 10, 8, 78, 275000, 5, 1, 4),
    24: (6, 8, 10, 76, 258000, 0, 1, 4),
    
    # Trúc Nhân songs
    25: (8, 6, 12, 80, 235000, 2, 1, 4),
    26: (7, 7, 10, 78, 248000, 7, 1, 4),
    
    # Vũ songs (indie)
    27: (4, 12, 6, 70, 285000, 4, 0, 4),
    28: (5, 14, 5, 68, 298000, 9, 0, 4),
    
    # MONO songs
    29: (6, 5, 8, 85, 242000, 1, 0, 4),
    30: (5, 6, 7, 82, 255000, 6, 0, 4),
}


def calculate_emotional_depth(song_data: dict) -> float:
    """
    Tính chiều sâu cảm xúc dựa trên:
    - Độ chênh lệch giữa valence và arousal
    - Mức độ acoustic
    - Speechiness (lyrics = emotion expression)
    - Thời lượng bài (bài dài thường sâu sắc hơn)
    
    Công thức: depth = base_depth + lyrics_factor + duration_factor + acoustic_bonus
    """
    valence = song_data.get('valence_score', 50)
    arousal = song_data.get('arousal_score', 50)
    acoustic = song_data.get('acousticness', 50)
    speechiness = song_data.get('speechiness', 5)
    duration = song_data.get('duration_ms', 240000)
    
    # Base depth từ VA distance (xa tâm = emotion mạnh hơn)
    va_dist = math.sqrt((valence - 50)**2 + (arousal - 50)**2)
    base_depth = min(100, va_dist * 1.5)
    
    # Lyrics factor (nhiều lời = express emotion nhiều hơn)
    lyrics_factor = speechiness * 0.3
    
    # Duration factor (bài dài > 4 phút thường sâu sắc hơn)
    duration_factor = min(20, (duration - 180000) / 10000) if duration > 180000 else 0
    
    # Acoustic bonus (nhạc acoustic thường emotional hơn)
    acoustic_bonus = acoustic * 0.15
    
    depth = base_depth + lyrics_factor + duration_factor + acoustic_bonus
    return round(min(100, max(0, depth)), 2)


def calculate_mood_stability(song_data: dict) -> float:
    """
    Tính độ ổn định tâm trạng:
    - Bài có tempo ổn định, không quá extreme = stability cao
    - Bài có arousal moderate = stability cao
    - Loudness không quá cao = stability cao
    
    Công thức: stability = 100 - volatility_score
    """
    arousal = song_data.get('arousal_score', 50)
    loudness = song_data.get('loudness', -8)
    tempo = song_data.get('tempo', 120)
    energy = song_data.get('energy', 50)
    
    # Arousal volatility (arousal extreme = less stable)
    arousal_vol = abs(arousal - 50) * 0.5
    
    # Loudness volatility (loud = less stable)
    loud_normalized = min(100, max(0, (loudness + 20) * 5))  # -20 to 0 -> 0 to 100
    loud_vol = loud_normalized * 0.2
    
    # Tempo volatility (fast tempo = less stable, nhưng không quá 180)
    tempo_vol = max(0, (tempo - 100) * 0.15) if tempo > 100 else 0
    
    # Energy volatility
    energy_vol = max(0, (energy - 60) * 0.2) if energy > 60 else 0
    
    total_volatility = arousal_vol + loud_vol + tempo_vol + energy_vol
    stability = 100 - min(100, total_volatility)
    return round(max(0, stability), 2)


def upgrade_database():
    """Nâng cấp database với các cột mới và dữ liệu."""
    print("=" * 60)
    print("🎵 NÂNG CẤP DATABASE MUSIC.DB v3.1.0")
    print("=" * 60)
    
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cursor = con.cursor()
    
    # 1. Thêm các cột mới nếu chưa có
    new_columns = [
        ("duration_ms", "INTEGER"),
        ("key", "INTEGER"),           # 0-11: C, C#, D, D#, E, F, F#, G, G#, A, A#, B
        ("mode", "INTEGER"),          # 0=minor, 1=major
        ("time_signature", "INTEGER"),
        ("emotional_depth", "REAL"),
        ("mood_stability", "REAL"),
    ]
    
    # Lấy danh sách cột hiện tại
    cursor.execute("PRAGMA table_info(songs)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    print("\n📊 Thêm cột mới:")
    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE songs ADD COLUMN {col_name} {col_type}")
            print(f"  ✅ Thêm cột: {col_name} ({col_type})")
        else:
            print(f"  ⏭️  Đã có: {col_name}")
    
    # 2. Cập nhật dữ liệu cho từng bài hát
    print("\n🔄 Cập nhật thuộc tính bài hát:")
    cursor.execute("SELECT song_id, song_name, artist, valence_score, arousal_score, acousticness, loudness, tempo, energy FROM songs")
    songs = cursor.fetchall()
    
    updated = 0
    for song in songs:
        song_id = song['song_id']
        
        # Lấy dữ liệu ước lượng hoặc tạo ngẫu nhiên hợp lý
        if song_id in SONG_ATTRIBUTES_ESTIMATES:
            attrs = SONG_ATTRIBUTES_ESTIMATES[song_id]
            speechiness, instrumentalness, liveness, popularity, duration_ms, key, mode, time_signature = attrs
        else:
            # Tạo dữ liệu hợp lý dựa trên các thuộc tính hiện có
            energy = song['energy'] or 50
            acousticness = song['acousticness'] or 50
            
            speechiness = random.randint(3, 12)  # Nhạc Việt ít speechiness hơn rap
            instrumentalness = max(0, min(100, 100 - energy + random.randint(-10, 10)))
            liveness = random.randint(5, 15)  # Studio recordings
            popularity = random.randint(60, 85)
            duration_ms = random.randint(200000, 320000)
            key = random.randint(0, 11)
            mode = random.choice([0, 1])
            time_signature = 4  # Hầu hết là 4/4
        
        # Tạo dict để tính emotional_depth và mood_stability
        song_data = {
            'valence_score': song['valence_score'] or 50,
            'arousal_score': song['arousal_score'] or 50,
            'acousticness': song['acousticness'] or 50,
            'speechiness': speechiness,
            'duration_ms': duration_ms,
            'loudness': song['loudness'] or -8,
            'tempo': song['tempo'] or 120,
            'energy': song['energy'] or 50,
        }
        
        emotional_depth = calculate_emotional_depth(song_data)
        mood_stability = calculate_mood_stability(song_data)
        
        # Cập nhật database
        cursor.execute("""
            UPDATE songs SET
                speechiness = ?,
                instrumentalness = ?,
                liveness = ?,
                popularity = ?,
                duration_ms = ?,
                key = ?,
                mode = ?,
                time_signature = ?,
                emotional_depth = ?,
                mood_stability = ?
            WHERE song_id = ?
        """, (speechiness, instrumentalness, liveness, popularity, duration_ms, 
              key, mode, time_signature, emotional_depth, mood_stability, song_id))
        
        updated += 1
        song_name = song['song_name']
        artist = song['artist']
        print(f"  [{song_id:2}] {song_name[:20]:20} - {artist[:15]:15} | depth={emotional_depth:5.1f} | stability={mood_stability:5.1f}")
    
    con.commit()
    
    # 3. Hiển thị thống kê
    print("\n" + "=" * 60)
    print("📈 THỐNG KÊ SAU NÂNG CẤP")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            AVG(emotional_depth) as avg_depth,
            AVG(mood_stability) as avg_stability,
            AVG(speechiness) as avg_speech,
            AVG(popularity) as avg_pop
        FROM songs
    """)
    stats = cursor.fetchone()
    print(f"  Emotional Depth TB:  {stats['avg_depth']:.1f}")
    print(f"  Mood Stability TB:   {stats['avg_stability']:.1f}")
    print(f"  Speechiness TB:      {stats['avg_speech']:.1f}")
    print(f"  Popularity TB:       {stats['avg_pop']:.1f}")
    
    # Thống kê theo mood
    cursor.execute("""
        SELECT mood, 
            COUNT(*) as count,
            AVG(emotional_depth) as avg_depth,
            AVG(mood_stability) as avg_stability
        FROM songs
        GROUP BY mood
    """)
    print("\n📊 Phân bố theo mood:")
    for row in cursor.fetchall():
        print(f"  {row['mood']:12} | {row['count']:2} bài | depth={row['avg_depth']:5.1f} | stability={row['avg_stability']:5.1f}")
    
    con.close()
    print("\n✅ Nâng cấp hoàn tất! Database version: 3.1.0")
    print(f"   Đã cập nhật {updated} bài hát với các thuộc tính mới.")
    

if __name__ == "__main__":
    upgrade_database()
