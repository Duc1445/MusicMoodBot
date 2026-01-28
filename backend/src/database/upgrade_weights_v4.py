"""
Database Upgrade v4.0 - Thêm các trọng số chi tiết để cải thiện mood prediction.

Các trọng số mới:
1. harmonic_complexity - Độ phức tạp hòa âm (key changes, chord progressions)
2. rhythmic_complexity - Độ phức tạp nhịp điệu (syncopation, polyrhythms)
3. vocal_presence - Mức độ có giọng hát (0=instrumental, 100=full vocal)
4. lyrical_density - Mật độ lời (ít/nhiều lời)
5. dynamic_range - Độ biến thiên âm lượng (soft-loud contrast)
6. melodic_brightness - Độ sáng của giai điệu (high vs low pitch)
7. tension_level - Mức căng thẳng âm nhạc (dissonance, unresolved chords)
8. groove_factor - Độ "groove" (rhythmic feel, pocket)
9. atmospheric_depth - Độ sâu không gian (reverb, ambient layers)
10. emotional_volatility - Độ biến đổi cảm xúc trong bài
11. cultural_familiarity - Độ quen thuộc văn hóa (mainstream vs niche)
12. nostalgia_factor - Yếu tố hoài niệm (retro sounds, classic progressions)
13. energy_buildup - Độ tăng năng lượng qua bài (crescendo effect)
14. release_satisfaction - Mức độ "thỏa mãn" khi đến đỉnh/hook
15. morning_score - Phù hợp buổi sáng (0-100)
16. evening_score - Phù hợp buổi tối (0-100)
17. workout_score - Phù hợp tập thể dục (0-100)
18. focus_score - Phù hợp tập trung/làm việc (0-100)
19. relax_score - Phù hợp thư giãn (0-100)
20. party_score - Phù hợp tiệc tùng (0-100)
"""

import sqlite3
import os
import math
import random

# Đường dẫn database
DB_PATH = os.path.join(os.path.dirname(__file__), "music.db")


def calculate_harmonic_complexity(song: dict) -> float:
    """
    Độ phức tạp hòa âm dựa trên key, mode và genre.
    Rock/Jazz cao hơn, Pop đơn giản hơn.
    """
    key = song.get("key", 0) or 0
    mode = song.get("mode", 1) or 1
    genre = (song.get("genre") or "").lower()
    
    base = 50.0
    
    # Genre influence
    if any(g in genre for g in ["rock", "metal", "progressive"]):
        base += 15
    elif any(g in genre for g in ["jazz", "blues", "soul"]):
        base += 20
    elif any(g in genre for g in ["electronic", "edm", "techno"]):
        base += 10
    elif any(g in genre for g in ["pop", "ballad"]):
        base -= 10
    
    # Key influence (sharps/flats = more complex)
    if key in [1, 3, 6, 8, 10]:  # black keys = more complex
        base += 8
    
    # Minor mode tends to have more complex harmony
    if mode == 0:
        base += 5
    
    return max(0, min(100, base + random.uniform(-5, 5)))


def calculate_rhythmic_complexity(song: dict) -> float:
    """
    Độ phức tạp nhịp điệu dựa trên tempo, time signature, danceability.
    """
    tempo = song.get("tempo", 120) or 120
    time_sig = song.get("time_signature", 4) or 4
    danceability = song.get("danceability", 50) or 50
    genre = (song.get("genre") or "").lower()
    
    base = 50.0
    
    # Tempo influence (very fast or very slow = less predictable)
    if tempo > 150 or tempo < 70:
        base += 10
    
    # Non-4/4 time signature = more complex
    if time_sig != 4:
        base += 20
    
    # Low danceability often means complex rhythm
    if danceability < 40:
        base += 10
    elif danceability > 75:
        base -= 5  # Very danceable = simpler rhythm
    
    # Genre influence
    if any(g in genre for g in ["progressive", "math rock", "jazz"]):
        base += 15
    elif any(g in genre for g in ["edm", "dance", "disco"]):
        base -= 10
    
    return max(0, min(100, base + random.uniform(-5, 5)))


def calculate_vocal_presence(song: dict) -> float:
    """
    Mức độ có giọng hát (0=instrumental, 100=full vocal).
    """
    instrumentalness = song.get("instrumentalness", 0) or 0
    speechiness = song.get("speechiness", 5) or 5
    
    # Inverse of instrumentalness
    vocal = 100 - instrumentalness
    
    # Speechiness adds to vocal presence
    vocal += speechiness * 0.3
    
    return max(0, min(100, vocal))


def calculate_lyrical_density(song: dict) -> float:
    """
    Mật độ lời (ít/nhiều lời).
    Dựa trên speechiness và duration.
    """
    speechiness = song.get("speechiness", 5) or 5
    instrumentalness = song.get("instrumentalness", 0) or 0
    
    if instrumentalness > 70:
        return 10  # Mostly instrumental
    
    # Speechiness correlates with lyrical density
    density = speechiness * 2.5 + 30
    
    return max(0, min(100, density + random.uniform(-10, 10)))


def calculate_dynamic_range(song: dict) -> float:
    """
    Độ biến thiên âm lượng (soft-loud contrast).
    Ballad có dynamic range cao, EDM thường compressed.
    """
    loudness = song.get("loudness", -8) or -8
    energy = song.get("energy", 50) or 50
    genre = (song.get("genre") or "").lower()
    
    # Loudness near 0 = heavily compressed = low dynamic range
    base = 50.0
    
    if loudness < -10:
        base += 20  # More quiet = likely more dynamic
    elif loudness > -4:
        base -= 15  # Very loud = compressed
    
    # Genre influence
    if any(g in genre for g in ["classical", "ballad", "acoustic"]):
        base += 15
    elif any(g in genre for g in ["edm", "metal", "pop"]):
        base -= 10
    
    return max(0, min(100, base + random.uniform(-5, 5)))


def calculate_melodic_brightness(song: dict) -> float:
    """
    Độ sáng của giai điệu (high vs low pitch).
    Based on key and happiness.
    """
    key = song.get("key", 0) or 0
    happiness = song.get("happiness", 50) or 50
    mode = song.get("mode", 1) or 1
    
    # Higher keys tend to sound brighter
    # Key: 0=C, 1=C#, ... 11=B
    key_brightness = {
        0: 50, 1: 55, 2: 60, 3: 45, 4: 65, 5: 55,
        6: 40, 7: 70, 8: 50, 9: 75, 10: 45, 11: 80
    }
    
    base = key_brightness.get(key, 50)
    
    # Happiness correlates with brightness
    base += (happiness - 50) * 0.3
    
    # Major = brighter
    if mode == 1:
        base += 10
    
    return max(0, min(100, base))


def calculate_tension_level(song: dict) -> float:
    """
    Mức căng thẳng âm nhạc (dissonance, unresolved chords).
    """
    happiness = song.get("happiness", 50) or 50
    energy = song.get("energy", 50) or 50
    mode = song.get("mode", 1) or 1
    loudness = song.get("loudness", -8) or -8
    genre = (song.get("genre") or "").lower()
    
    # Low happiness + high energy = tension
    base = (100 - happiness) * 0.4 + energy * 0.3
    
    # Minor mode = more tension
    if mode == 0:
        base += 10
    
    # Loud = more tension
    if loudness > -6:
        base += 10
    
    # Genre influence
    if any(g in genre for g in ["metal", "rock", "punk"]):
        base += 15
    elif any(g in genre for g in ["ambient", "chill", "lofi"]):
        base -= 20
    
    return max(0, min(100, base))


def calculate_groove_factor(song: dict) -> float:
    """
    Độ "groove" (rhythmic feel, pocket).
    High danceability + moderate tempo = good groove.
    """
    danceability = song.get("danceability", 50) or 50
    tempo = song.get("tempo", 120) or 120
    energy = song.get("energy", 50) or 50
    genre = (song.get("genre") or "").lower()
    
    # Danceability is the main factor
    base = danceability * 0.6
    
    # Tempo sweet spot (90-130 BPM)
    if 90 <= tempo <= 130:
        base += 20
    elif tempo > 160 or tempo < 70:
        base -= 10
    
    # Moderate energy = better groove
    if 40 <= energy <= 80:
        base += 10
    
    # Genre influence
    if any(g in genre for g in ["funk", "disco", "r&b", "soul", "hip-hop"]):
        base += 15
    
    return max(0, min(100, base))


def calculate_atmospheric_depth(song: dict) -> float:
    """
    Độ sâu không gian (reverb, ambient layers).
    """
    acousticness = song.get("acousticness", 50) or 50
    instrumentalness = song.get("instrumentalness", 0) or 0
    liveness = song.get("liveness", 10) or 10
    genre = (song.get("genre") or "").lower()
    
    base = 50.0
    
    # Acoustic instruments have natural depth
    base += acousticness * 0.2
    
    # Instrumental music often has more atmosphere
    base += instrumentalness * 0.15
    
    # Live recordings have natural reverb
    base += liveness * 0.1
    
    # Genre influence
    if any(g in genre for g in ["ambient", "electronic", "post-rock", "shoegaze"]):
        base += 20
    elif any(g in genre for g in ["punk", "hardcore"]):
        base -= 15
    
    return max(0, min(100, base))


def calculate_emotional_volatility(song: dict) -> float:
    """
    Độ biến đổi cảm xúc trong bài.
    High energy variance, low mood stability = high volatility.
    """
    mood_stability = song.get("mood_stability", 70) or 70
    energy = song.get("energy", 50) or 50
    genre = (song.get("genre") or "").lower()
    
    # Inverse of stability
    base = 100 - mood_stability
    
    # High energy songs tend to have more emotional peaks
    base += (energy - 50) * 0.2
    
    # Genre influence
    if any(g in genre for g in ["progressive", "post-rock", "classical"]):
        base += 15  # These genres have more dynamic journeys
    elif any(g in genre for g in ["lofi", "ambient", "chill"]):
        base -= 20
    
    return max(0, min(100, base + random.uniform(-5, 5)))


def calculate_cultural_familiarity(song: dict) -> float:
    """
    Độ quen thuộc văn hóa (mainstream vs niche).
    Based on popularity and genre.
    """
    popularity = song.get("popularity", 50) or 50
    genre = (song.get("genre") or "").lower()
    
    base = popularity * 0.6 + 20
    
    # Mainstream genres
    if any(g in genre for g in ["pop", "ballad", "vpop", "dance"]):
        base += 15
    elif any(g in genre for g in ["experimental", "noise", "avant-garde"]):
        base -= 20
    
    return max(0, min(100, base))


def calculate_nostalgia_factor(song: dict) -> float:
    """
    Yếu tố hoài niệm (retro sounds, classic progressions).
    """
    acousticness = song.get("acousticness", 50) or 50
    genre = (song.get("genre") or "").lower()
    tempo = song.get("tempo", 120) or 120
    
    base = 40.0
    
    # Acoustic = more nostalgic feel
    base += acousticness * 0.3
    
    # Moderate tempo = nostalgic
    if 80 <= tempo <= 120:
        base += 10
    
    # Genre influence
    if any(g in genre for g in ["ballad", "acoustic", "folk", "oldies"]):
        base += 20
    elif any(g in genre for g in ["edm", "dubstep", "trap"]):
        base -= 20
    
    return max(0, min(100, base + random.uniform(-5, 5)))


def calculate_energy_buildup(song: dict) -> float:
    """
    Độ tăng năng lượng qua bài (crescendo effect).
    EDM and progressive genres have high buildup.
    """
    energy = song.get("energy", 50) or 50
    genre = (song.get("genre") or "").lower()
    duration = song.get("duration_ms", 200000) or 200000
    
    base = 50.0
    
    # High energy songs often have buildups
    base += (energy - 50) * 0.3
    
    # Longer songs have more room for buildup
    if duration > 300000:  # > 5 min
        base += 10
    
    # Genre influence
    if any(g in genre for g in ["edm", "trance", "progressive", "post-rock"]):
        base += 25
    elif any(g in genre for g in ["punk", "acoustic"]):
        base -= 15
    
    return max(0, min(100, base + random.uniform(-5, 5)))


def calculate_release_satisfaction(song: dict) -> float:
    """
    Mức độ "thỏa mãn" khi đến đỉnh/hook.
    High danceability + high energy peaks = satisfaction.
    """
    danceability = song.get("danceability", 50) or 50
    energy = song.get("energy", 50) or 50
    happiness = song.get("happiness", 50) or 50
    
    # Combine factors
    base = (danceability * 0.3 + energy * 0.3 + happiness * 0.4)
    
    return max(0, min(100, base + random.uniform(-5, 5)))


def calculate_context_scores(song: dict) -> dict:
    """
    Tính các điểm phù hợp theo ngữ cảnh sử dụng.
    """
    energy = song.get("energy", 50) or 50
    happiness = song.get("happiness", 50) or 50
    tempo = song.get("tempo", 120) or 120
    danceability = song.get("danceability", 50) or 50
    acousticness = song.get("acousticness", 50) or 50
    
    # Morning: Moderate energy, positive mood
    morning = (happiness * 0.4 + 
               max(0, 80 - abs(energy - 60)) +  # Sweet spot around 60
               max(0, 80 - abs(tempo - 110)) * 0.3)  # Moderate tempo
    
    # Evening: Lower energy, can be sad or happy
    evening = (acousticness * 0.3 +
               max(0, 100 - energy) * 0.4 +
               max(0, 80 - abs(tempo - 90)) * 0.3)
    
    # Workout: High energy, fast tempo
    workout = (energy * 0.5 +
               min(100, tempo / 1.5) * 0.3 +
               danceability * 0.2)
    
    # Focus: Low vocal, moderate energy, not too catchy
    focus = (max(0, 100 - danceability) * 0.3 +
             max(0, 80 - abs(energy - 50)) * 0.3 +
             acousticness * 0.2 +
             song.get("instrumentalness", 0) * 0.2)
    
    # Relax: Low energy, acoustic, slow
    relax = (acousticness * 0.3 +
             max(0, 100 - energy) * 0.4 +
             max(0, 100 - tempo / 1.5) * 0.3)
    
    # Party: High energy, danceable, loud
    party = (energy * 0.35 +
             danceability * 0.35 +
             (100 + song.get("loudness", -8)) * 0.3)
    
    return {
        "morning_score": max(0, min(100, morning)),
        "evening_score": max(0, min(100, evening)),
        "workout_score": max(0, min(100, workout)),
        "focus_score": max(0, min(100, focus)),
        "relax_score": max(0, min(100, relax)),
        "party_score": max(0, min(100, party))
    }


def upgrade_database():
    """Thêm các cột trọng số mới vào database."""
    
    new_columns = [
        # Complexity metrics
        ("harmonic_complexity", "REAL"),
        ("rhythmic_complexity", "REAL"),
        
        # Vocal metrics
        ("vocal_presence", "REAL"),
        ("lyrical_density", "REAL"),
        
        # Audio characteristics
        ("dynamic_range", "REAL"),
        ("melodic_brightness", "REAL"),
        ("tension_level", "REAL"),
        ("groove_factor", "REAL"),
        ("atmospheric_depth", "REAL"),
        
        # Emotional metrics
        ("emotional_volatility", "REAL"),
        ("cultural_familiarity", "REAL"),
        ("nostalgia_factor", "REAL"),
        ("energy_buildup", "REAL"),
        ("release_satisfaction", "REAL"),
        
        # Context scores
        ("morning_score", "REAL"),
        ("evening_score", "REAL"),
        ("workout_score", "REAL"),
        ("focus_score", "REAL"),
        ("relax_score", "REAL"),
        ("party_score", "REAL"),
    ]
    
    print("=" * 60)
    print("🎵 Music Database Upgrade v4.0")
    print("   Thêm 20 trọng số chi tiết mới")
    print("=" * 60)
    
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    # Thêm các cột mới
    print("\n📊 Thêm các cột mới...")
    for col_name, col_type in new_columns:
        try:
            cur.execute(f"ALTER TABLE songs ADD COLUMN {col_name} {col_type}")
            print(f"   ✅ Thêm cột: {col_name}")
        except sqlite3.OperationalError:
            print(f"   ⏭️  Cột đã tồn tại: {col_name}")
    
    con.commit()
    
    # Lấy tất cả bài hát
    cur.execute("SELECT * FROM songs")
    songs = [dict(row) for row in cur.fetchall()]
    
    print(f"\n🔄 Tính toán trọng số cho {len(songs)} bài hát...")
    
    for i, song in enumerate(songs, 1):
        song_id = song["song_id"]
        
        # Tính các trọng số mới
        harmonic_complexity = calculate_harmonic_complexity(song)
        rhythmic_complexity = calculate_rhythmic_complexity(song)
        vocal_presence = calculate_vocal_presence(song)
        lyrical_density = calculate_lyrical_density(song)
        dynamic_range = calculate_dynamic_range(song)
        melodic_brightness = calculate_melodic_brightness(song)
        tension_level = calculate_tension_level(song)
        groove_factor = calculate_groove_factor(song)
        atmospheric_depth = calculate_atmospheric_depth(song)
        emotional_volatility = calculate_emotional_volatility(song)
        cultural_familiarity = calculate_cultural_familiarity(song)
        nostalgia_factor = calculate_nostalgia_factor(song)
        energy_buildup = calculate_energy_buildup(song)
        release_satisfaction = calculate_release_satisfaction(song)
        
        context_scores = calculate_context_scores(song)
        
        # Cập nhật database
        cur.execute("""
            UPDATE songs SET
                harmonic_complexity = ?,
                rhythmic_complexity = ?,
                vocal_presence = ?,
                lyrical_density = ?,
                dynamic_range = ?,
                melodic_brightness = ?,
                tension_level = ?,
                groove_factor = ?,
                atmospheric_depth = ?,
                emotional_volatility = ?,
                cultural_familiarity = ?,
                nostalgia_factor = ?,
                energy_buildup = ?,
                release_satisfaction = ?,
                morning_score = ?,
                evening_score = ?,
                workout_score = ?,
                focus_score = ?,
                relax_score = ?,
                party_score = ?
            WHERE song_id = ?
        """, (
            round(harmonic_complexity, 2),
            round(rhythmic_complexity, 2),
            round(vocal_presence, 2),
            round(lyrical_density, 2),
            round(dynamic_range, 2),
            round(melodic_brightness, 2),
            round(tension_level, 2),
            round(groove_factor, 2),
            round(atmospheric_depth, 2),
            round(emotional_volatility, 2),
            round(cultural_familiarity, 2),
            round(nostalgia_factor, 2),
            round(energy_buildup, 2),
            round(release_satisfaction, 2),
            round(context_scores["morning_score"], 2),
            round(context_scores["evening_score"], 2),
            round(context_scores["workout_score"], 2),
            round(context_scores["focus_score"], 2),
            round(context_scores["relax_score"], 2),
            round(context_scores["party_score"], 2),
            song_id
        ))
        
        print(f"   [{i}/{len(songs)}] {song.get('song_name', 'Unknown')} - {song.get('artist', 'Unknown')}")
        print(f"      Harmonic: {harmonic_complexity:.1f} | Rhythmic: {rhythmic_complexity:.1f}")
        print(f"      Tension: {tension_level:.1f} | Groove: {groove_factor:.1f}")
        print(f"      Morning: {context_scores['morning_score']:.1f} | Party: {context_scores['party_score']:.1f}")
    
    con.commit()
    
    # Thống kê
    print("\n" + "=" * 60)
    print("📊 THỐNG KÊ SAU NÂNG CẤP")
    print("=" * 60)
    
    stats_queries = [
        ("harmonic_complexity", "Harmonic Complexity"),
        ("rhythmic_complexity", "Rhythmic Complexity"),
        ("tension_level", "Tension Level"),
        ("groove_factor", "Groove Factor"),
        ("morning_score", "Morning Score"),
        ("party_score", "Party Score"),
    ]
    
    for col, label in stats_queries:
        cur.execute(f"SELECT AVG({col}), MIN({col}), MAX({col}) FROM songs")
        avg, min_val, max_val = cur.fetchone()
        print(f"   {label}: avg={avg:.1f}, min={min_val:.1f}, max={max_val:.1f}")
    
    con.close()
    
    print("\n✅ Hoàn thành nâng cấp database v4.0!")
    print(f"   📁 Database: {DB_PATH}")
    print(f"   🎵 Bài hát: {len(songs)}")
    print(f"   📊 Trọng số mới: 20")


if __name__ == "__main__":
    upgrade_database()
