import sqlite3
import os

# Use absolute path to src/database directory
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "music.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS songs (
    song_id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_name TEXT NOT NULL,
    artist TEXT NOT NULL,
    genre TEXT,
    
    -- Core audio features (0-100 or BPM/dB)
    energy INTEGER,                -- 0-100 (intensity/power)
    happiness INTEGER,             -- 0-100 (positivity/major key)
    danceability INTEGER,          -- 0-100 (rhythmic regularity)
    acousticness INTEGER,          -- 0-100 (acoustic vs electronic)
    tempo INTEGER,                 -- BPM (beats per minute, 0-250)
    loudness INTEGER,              -- dBFS (-60 to 0 dB, where -60=silent, 0=max)
    
    -- Optional enhanced features (0-100, for future training)
    speechiness INTEGER,           -- 0-100 (spoken words vs music)
    instrumentalness INTEGER,      -- 0-100 (no vocals)
    liveness INTEGER,              -- 0-100 (live performance indicator)
    popularity INTEGER,            -- 0-100 (global/chart popularity)
    
    -- Computed mood scores (auto-calculated by algorithm)
    valence_score REAL,            -- 0-100 (computed: 0.85*happiness + 0.15*danceability)
    arousal_score REAL,            -- 0-100 (computed: energy + weights*tempo/loudness/dance - acoustic_penalty)
    mood TEXT,                     -- energetic|happy|sad|stress|angry (auto-classified)
    intensity INTEGER,             -- 1=low|2=medium|3=high (derived from arousal)
    mood_confidence REAL,          -- 0-1 (Gaussian probability)
    
    -- Metadata
    source TEXT                    -- Data source: tunebat, spotify, youtube, manual
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS listening_history (
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

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_history_user 
ON listening_history(user_id, last_played DESC)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
)
""")

conn.commit()

# Add missing columns to existing database if upgrading
try:
    cursor.execute("ALTER TABLE songs ADD COLUMN speechiness INTEGER")
except:
    pass  # Column already exists

try:
    cursor.execute("ALTER TABLE songs ADD COLUMN instrumentalness INTEGER")
except:
    pass

try:
    cursor.execute("ALTER TABLE songs ADD COLUMN liveness INTEGER")
except:
    pass

try:
    cursor.execute("ALTER TABLE songs ADD COLUMN popularity INTEGER")
except:
    pass

try:
    cursor.execute("ALTER TABLE songs ADD COLUMN valence_score REAL")
except:
    pass

try:
    cursor.execute("ALTER TABLE songs ADD COLUMN arousal_score REAL")
except:
    pass

try:
    cursor.execute("ALTER TABLE songs ADD COLUMN mood_confidence REAL")
except:
    pass

try:
    cursor.execute("ALTER TABLE songs ADD COLUMN mood_score REAL")
except:
    pass

conn.commit()
conn.close()

print("✓ music.db schema updated successfully")

