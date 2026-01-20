# Repository Module

Data access layer implementing the Repository pattern for clean data abstraction.

## Files

### song_repo.py

Low-level database operations for song data.

#### Functions

**connect(db_path: str) -> sqlite3.Connection**

- Opens SQLite connection with row factory enabled
- Returns connection object ready for operations

**get_table_columns(con, table: str) -> List[str]**

- Retrieves list of column names from a table
- Useful for schema introspection

**ensure_columns(con, table: str, column_defs: List[str]) -> None**

- Adds missing columns to table
- Safe to run multiple times (idempotent)
- Example: `ensure_columns(con, "songs", ["mood TEXT", "mood_score REAL"])`

**fetch_songs(con, where: str, params: Tuple) -> List[Song]**

- Retrieves songs from database
- Supports optional WHERE clause with parameters
- Returns list of dictionaries

**fetch_song_by_id(con, song_id: int) -> Optional[Song]**

- Retrieves single song by ID
- Returns None if not found

**update_song(con, song_id: int, updates: Dict[str, object]) -> None**

- Updates song record with new values
- Example: `update_song(con, 42, {"mood": "happy", "intensity": 2})`

### history_repo.py

Repository for song mood history tracking.

#### Functions

(To be implemented based on history requirements)

## Usage

```python
from backend.src.repo.song_repo import (
    connect, fetch_songs, fetch_song_by_id, update_song, ensure_columns
)

# Connect to database
con = connect("music.db")

try:
    # Ensure debug columns exist
    ensure_columns(con, "songs", [
        "valence_score REAL",
        "arousal_score REAL",
        "mood_confidence REAL"
    ])

    # Fetch all songs
    all_songs = fetch_songs(con)

    # Fetch songs with WHERE clause
    unhappy_songs = fetch_songs(
        con,
        "mood IN (?, ?)",
        ("sad", "stress")
    )

    # Fetch single song
    song = fetch_song_by_id(con, song_id=42)
    if song:
        print(f"Song: {song['title']}")

    # Update song
    update_song(con, song_id=42, updates={
        "mood": "energetic",
        "intensity": 3,
        "mood_score": 85.5,
        "valence_score": 75.0,
        "arousal_score": 80.0,
        "mood_confidence": 0.92
    })

    con.commit()

finally:
    con.close()
```

## Design Principles

1. **Abstraction**: Database details hidden from services layer
2. **Composability**: Small functions combine for complex queries
3. **Type Safety**: Type hints for all parameters
4. **Idempotency**: Safe to run operations multiple times
5. **Context Management**: Always use try/finally for connections

## Query Patterns

### Fetch with WHERE Clause

```python
missing_mood_songs = fetch_songs(
    con,
    "mood IS NULL OR intensity IS NULL",
)
```

### Batch Updates

```python
songs = fetch_songs(con, "mood = ?", ("happy",))
for song in songs:
    # Process each song
    update_song(con, song["song_id"], {"intensity": 2})
con.commit()
```

### Conditional Column Addition

```python
if add_debug_cols:
    ensure_columns(con, "songs", [
        "valence_score REAL",
        "arousal_score REAL",
        "mood_confidence REAL"
    ])
```
