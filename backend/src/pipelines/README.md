# Pipelines Module

Machine learning model implementations for mood prediction.

## Files

### mood_engine.py

Core mood prediction model with Valence-Arousal (VA) + probabilistic prototypes approach.

#### Classes

**EngineConfig**

- Configuration dataclass for model parameters
- Tempo normalization bounds
- Feature weights for arousal calculation (energy, tempo, loudness, danceability, acousticness)
- Feature weights for valence calculation (happiness, danceability)
- Prototype training parameters
- Intensity level thresholds
- Genre adaptation settings

**Prototype2D**

- 2D Gaussian representation of a mood
- Tracks mean (μ) and standard deviation (σ) for valence and arousal
- Computes log-likelihood for probabilistic mood classification

**MoodEngine**

- Main model class
- Methods:
  - `fit(songs)`: Train model on songs data
  - `predict(song)`: Predict mood for a single song
  - `mood_probabilities(song, v, a)`: Get probability distribution over moods
  - `infer_intensity_int(arousal)`: Map arousal to intensity level (1-3)
  - `valence_score(song)`: Compute valence (happiness) from song features
  - `arousal_score(song)`: Compute arousal from song features

#### Model Logic

**Valence Calculation**

- Weighted combination of: happiness (0.85) + danceability (0.15)

**Arousal Calculation**

- Weighted combination of:
  - Energy (0.45)
  - Tempo normalized to 0-100 (0.20)
  - Loudness normalized from dBFS (0.20)
  - Danceability (0.10)
  - Minus acousticness penalty (0.05)

**Mood Classification**

1. Bootstrap weak labels from VA coordinates:
   - Energetic: High V, High A
   - Happy: High V, Low A
   - Sad: Low V, Low A
   - Stress: Low V, High A (default)
   - Angry: Low V, High A (if loud + fast)

2. Fit 2D Gaussian prototypes per mood

3. Use probabilistic approach to classify new songs

4. Support genre-specific prototypes (optional)

## Usage

```python
from backend.src.pipelines.mood_engine import MoodEngine, EngineConfig

# Create model with default config
engine = MoodEngine()

# Or use custom config
cfg = EngineConfig(
    w_energy=0.5,  # Increase energy weight
    use_genre_tokens=True
)
engine = MoodEngine(cfg=cfg)

# Train on songs
engine.fit(songs)

# Predict mood for a song
song = {"energy": 80, "valence": 70, "tempo": 120, ...}
result = engine.predict(song)
print(result)
# Output:
# {
#   "mood": "energetic",
#   "intensity": 3,
#   "mood_score": 75.0,
#   "valence_score": 70.0,
#   "arousal_score": 80.0,
#   "mood_confidence": 0.87
# }
```

## Feature Requirements

Songs must include these features:

- `energy`: 0-100 (can be Spotify-like 0-1)
- `valence`: 0-100 (happiness)
- `tempo`: BPM (beats per minute)
- `loudness`: dBFS or 0-100
- `danceability`: 0-100
- `acousticness`: 0-100
- `genre` (optional): For genre-based prototypes

## Customization

### Change Mood Thresholds

```python
cfg = EngineConfig(
    angry_loudness_hi=80.0,  # Increase threshold for "angry" classification
    angry_tempo_hi=75.0
)
```

### Adjust Feature Weights

```python
cfg = EngineConfig(
    w_energy=0.6,        # Increase importance of energy
    w_acoustic_penalty=0.1  # Reduce acousticness penalty
)
```

### Genre Adaptation

```python
cfg = EngineConfig(
    use_genre_tokens=True,   # Enable genre-specific prototypes
    genre_min_count=50,      # Minimum songs per genre
    genre_weight=0.6         # Blend 40% global + 60% genre
)
```
