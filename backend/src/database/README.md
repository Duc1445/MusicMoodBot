# Database Module

Handles SQLite database initialization, schema management, and sample data seeding.

## Files

### init_db.py

- Creates SQLite database and tables
- Initializes `songs` table with schema:
  - `song_id` (INTEGER PRIMARY KEY)
  - Standard audio features: `energy`, `valence`, `tempo`, `loudness`, `danceability`, `acousticness`, etc.
  - Mood prediction columns: `mood`, `intensity`, `mood_score`
  - Optional debug columns: `valence_score`, `arousal_score`, `mood_confidence`
- Idempotent: Safe to run multiple times

### seed_data.py

- Populates database with sample songs
- Useful for testing and development
- Can be extended with data from music APIs (Spotify, TuneBat, etc.)

### music.sqbpro

- SQLite database file (auto-created by init_db.py)
- Contains all song metadata and predictions

## Usage

### Initialize Database Schema

```bash
python -m backend.src.database.init_db
```

### Seed Sample Data

```bash
python -m backend.src.database.seed_data
```

### View Database

Use SQLite viewer or:

```bash
sqlite3 music.sqbpro
sqlite> SELECT * FROM songs LIMIT 5;
```

## Database Schema

### songs table

```
CREATE TABLE songs (
    song_id INTEGER PRIMARY KEY,
    title TEXT,
    artist TEXT,
    genre TEXT,
    energy INTEGER,              -- 0-100
    valence INTEGER,             -- 0-100 (happiness)
    tempo REAL,                  -- BPM
    loudness REAL,               -- dBFS
    danceability INTEGER,        -- 0-100
    acousticness INTEGER,        -- 0-100
    mood TEXT,                   -- energetic|happy|sad|stress|angry
    intensity INTEGER,           -- 1|2|3 (low|medium|high)
    mood_score REAL,             -- 0-100 (sortable index)

    -- Debug columns (optional)
    valence_score REAL,          -- Model's computed valence 0-100
    arousal_score REAL,          -- Model's computed arousal 0-100
    mood_confidence REAL         -- Model confidence 0-1
);
```

## Data Sources

You can populate this database from:

- **Spotify API**: energy, valence, tempo, danceability, acousticness
- **TuneBat API**: music features and mood annotations
- **Last.fm API**: Genre and metadata
- **Manual CSV import**: For testing or custom data
