import sqlite3

conn = sqlite3.connect("music.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS songs (
    song_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    genre TEXT,
    
    -- Audio features (0-100 or BPM/dBFS)
    energy INTEGER,                -- 0-100 (Spotify/TuneBat energy)
    valence INTEGER,               -- 0-100 (Spotify/TuneBat valence/happiness)
    danceability INTEGER,          -- 0-100
    acousticness INTEGER,          -- 0-100
    tempo REAL,                    -- BPM (beats per minute)
    loudness REAL,                 -- dBFS (-60 to 0)
    
    -- Mood prediction columns
    mood TEXT,                     -- energetic|happy|sad|stress|angry
    intensity INTEGER,             -- 1=low|2=medium|3=high
    mood_score REAL,               -- 0-100 sortable score
    
    -- Debug/analysis columns (optional)
    valence_score REAL,            -- Model's computed valence
    arousal_score REAL,            -- Model's computed arousal
    mood_confidence REAL           -- Model confidence 0-1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS recommendation_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER,
    recommend_date DATE,
    session_id TEXT,
    mood TEXT,
    FOREIGN KEY (song_id) REFERENCES songs(song_id)
)
""")

conn.commit()
conn.close()

print("music.db created successfully")
