# Services Module

Core business logic and orchestration layer for the music mood engine.

## Module Files

### constants.py

Shared type definitions and constants:

- `Song`: Type alias for song dictionary
- `MOODS`: List of available mood categories ("energetic", "happy", "sad", "stress", "angry")
- `TABLE_SONGS`: Database table name

### helpers.py

Pure utility functions for data normalization and processing:

- **\_is_missing()**: Check if value is None or NaN
- **\_to_float()**: Safe float conversion with fallback
- **clamp()**: Constrain value to range
- **percentile()**: Calculate percentile without numpy
- **robust_minmax()**: Normalize to 0-100 scale
- **coerce_0_100()**: Convert 0-1 or 0-100 scales to consistent 0-100
- **normalize_loudness_to_0_100()**: Handle dBFS to 0-100 conversion
- **softmax()**: Compute probability distribution from logits
- **tokenize_genre()**: Parse mixed genre strings (e.g., "ballad+rock, pop")

### mood_services.py

High-level mood prediction service:

- **DBMoodEngine**: Main service class with caching
  - `fit()`: Fit model to all songs in database
  - `predict_one()`: Predict mood for a single song
  - `update_one()`: Update database with prediction for one song
  - `update_missing()`: Update all songs with NULL mood values
  - `update_all()`: Recompute all songs
  - Auto-refitting when song count changes

### history_service.py

Manage song mood history and tracking:

- Stores mood prediction history for songs
- Enables trend analysis and tracking mood changes

### ranking_service.py

Rank songs based on mood criteria:

- Sort by mood type
- Filter by intensity level
- Custom ranking algorithms

## Usage Example

```python
from backend.src.services.mood_services import DBMoodEngine

# Create engine with automatic model refitting
engine = DBMoodEngine(
    db_path="music.db",
    add_debug_cols=True,      # Store valence/arousal scores
    auto_fit=True,            # Auto-fit model on first use
    refit_on_change=True      # Re-fit if song count changes
)

# Fit model to current data
engine.fit(force=True)

# Update songs with NULL mood values
count = engine.update_missing()
print(f"Updated {count} rows")

# Update all songs
count = engine.update_all()
print(f"Recomputed {count} songs")

# Predict mood for a single song
song_dict = {"energy": 80, "valence": 70, "tempo": 120, ...}
result = engine.predict_one(song_dict)
print(f"Mood: {result['mood']}, Intensity: {result['intensity']}")
```

## Configuration

Customize model behavior via `EngineConfig` in mood_engine.py:

- Tempo normalization bounds
- Feature weights (energy, tempo, loudness, danceability)
- Intensity thresholds
- Genre token adaptation parameters
