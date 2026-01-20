# Backend - Music Mood Engine

## Overview

The backend is a Python-based music mood prediction and analysis engine. It reads song metadata from SQLite, applies machine learning models (Valence-Arousal model), and predicts mood classifications with intensity levels.

## Architecture

```
backend/
├── main.py                 # Entry point and CLI
├── requirements.txt        # Dependencies
└── src/
    ├── api/                # REST API endpoints
    │   └── mood_api.py
    ├── database/           # Database initialization & seeding
    │   ├── init_db.py
    │   ├── seed_data.py
    │   └── music.sqbpro
    ├── pipelines/          # ML model implementations
    │   └── mood_engine.py
    ├── repo/               # Data access layer (Repository pattern)
    │   ├── history_repo.py
    │   └── song_repo.py
    └── services/           # Business logic & orchestration
        ├── constants.py    # Shared constants (Song, MOODS, etc.)
        ├── helpers.py      # Utility functions (clamp, percentile, softmax, etc.)
        ├── mood_services.py    # DBMoodEngine service class
        ├── history_service.py  # Song history management
        └── ranking_service.py  # Song ranking logic
```

## Key Components

### Services Layer

- **constants.py**: Centralized type definitions and constants
- **helpers.py**: Pure utility functions for data normalization and processing
- **mood_services.py**: High-level `DBMoodEngine` class for mood predictions with caching
- **history_service.py**: Manages song mood history
- **ranking_service.py**: Ranks songs based on moods and other criteria

### Pipelines Layer

- **mood_engine.py**: Core ML model implementation
  - `MoodEngine`: VA (Valence-Arousal) + probabilistic prototypes
  - `EngineConfig`: Configurable model parameters
  - `Prototype2D`: 2D Gaussian prototype for mood representation

### Repository Layer

- **song_repo.py**: Database operations (CRUD for songs)
- **history_repo.py**: Song history tracking

### Database Layer

- Automatically creates and manages SQLite schema
- Supports debug columns for model interpretability

## Features

✅ **Mood Prediction**: Classifies songs into 5 moods:

- Energetic (High Valence, High Arousal)
- Happy (High Valence, Low Arousal)
- Sad (Low Valence, Low Arousal)
- Stress (Low Valence, High Arousal)
- Angry (Proxy based on loudness & tempo)

✅ **Intensity Levels**: 1 (Low), 2 (Medium), 3 (High)

✅ **Probabilistic Approach**: Uses 2D Gaussian prototypes per mood

✅ **Genre Adaptation**: Token-based genre prototypes (e.g., "ballad+rock")

✅ **Automatic Refitting**: Re-fits model when song count changes

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Initialize Database

```bash
python -m backend.src.database.init_db
python -m backend.src.database.seed_data
```

### Predict Mood for Missing Songs

```python
from backend.src.services.mood_services import DBMoodEngine

engine = DBMoodEngine("music.db", add_debug_cols=True)
engine.update_missing()  # Fill NULL mood values
```

### Update Single Song

```python
engine.update_one(song_id=12)
```

### Recompute All Songs

```python
engine.update_all()
```

## Configuration

Edit `EngineConfig` in `mood_engine.py` to adjust:

- Weight for energy, tempo, loudness, danceability
- Intensity thresholds
- Prototype training parameters
- Genre token adaptation settings

## Testing

```bash
python main.py --db music.db update-missing --debug-cols
python main.py --db music.db update-all
python main.py --db music.db update-one --id 42
```

## Development

### Code Structure Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **DRY**: Helper functions extracted to avoid duplication
3. **Type Safety**: Full type hints throughout
4. **Testability**: Pure functions where possible
5. **Extensibility**: Config classes for easy customization
