"""
Backend Core Module
===================
Contains the core ML/NLP engines for mood prediction and playlist curation.

This module re-exports from pipelines/ for clean imports.
The actual implementations are in pipelines/ folder.

Usage:
    from backend.core import MoodEngine, EngineConfig
    from backend.core import CuratorEngine, CuratorConfig
"""

# Re-export from pipelines (canonical location)
from backend.src.pipelines.mood_engine import (
    MoodEngine,
    EngineConfig,
)

from backend.src.pipelines.curator_engine import (
    CuratorEngine,
    CuratorConfig,
)

from backend.src.pipelines.text_mood_detector import (
    TextMoodDetector,
    text_mood_detector,  # Singleton instance
)

from backend.src.pipelines.song_similarity import (
    SongSimilarityEngine,
    get_similarity_engine,
)

from backend.src.pipelines.mood_transition import (
    MoodTransitionEngine,
    get_transition_engine,
    TransitionSpeed,
)

from backend.src.pipelines.curator_types import (
    CuratorTrack,
    PlaylistState,
    TextureType,
    camelot_distance,
    is_harmonic_compatible,
    texture_transition_score,
    detect_texture,
)

__all__ = [
    # Mood Engine
    "MoodEngine",
    "EngineConfig",
    # Curator Engine
    "CuratorEngine",
    "CuratorConfig",
    # Text Mood Detector
    "TextMoodDetector",
    "text_mood_detector",
    # Song Similarity
    "SongSimilarityEngine",
    "get_similarity_engine",
    # Mood Transition
    "MoodTransitionEngine",
    "get_transition_engine",
    "TransitionSpeed",
    # Types
    "CuratorTrack",
    "PlaylistState",
    "TextureType",
    "camelot_distance",
    "is_harmonic_compatible",
    "texture_transition_score",
    "detect_texture",
]
