"""
Services Package - Phase 2 Architecture
========================================

This package contains the core service modules for the Music Chatbot Backend.

Modules:
    schema: Song dataclass and Enums (Mood, TextureType)
    mood_engine: MoodEngine v5.2 (Perception Layer)
    curator_engine: CuratorEngine v2.0 (Narrative Layer)
    narrative: NarrativeAdapter v2.0 (UX Layer)
    
Legacy Modules:
    constants: Legacy constants (maintained for backward compatibility)
    helpers: Utility functions
    mood_services: DBMoodEngine wrapper
"""

# Phase 2 exports
from backend.src.services.schema import (
    Song,
    Mood,
    TextureType,
    Intensity,
    MOODS,
    key_mode_to_camelot,
    camelot_distance,
    is_harmonic_compatible,
    texture_transition_score,
)

from backend.src.services.mood_engine import (
    MoodEngine,
    EngineConfig,
    Prototype2D,
    get_arousal_label,
    get_valence_label,
)

from backend.src.services.curator_engine import (
    CuratorEngine,
    CuratorConfig,
    PlaylistState,
    EnergyCurveTemplates,
)

from backend.src.services.narrative import (
    NarrativeAdapter,
    NarrativeGenerator,
    PlaylistTheme,
    generate_playlist_narrative,
    explain_playlist_theme,
    generate_song_explanation,
    detect_playlist_theme,
)

__all__ = [
    # Schema
    "Song",
    "Mood",
    "TextureType",
    "Intensity",
    "MOODS",
    "key_mode_to_camelot",
    "camelot_distance",
    "is_harmonic_compatible",
    "texture_transition_score",
    # MoodEngine
    "MoodEngine",
    "EngineConfig",
    "Prototype2D",
    "get_arousal_label",
    "get_valence_label",
    # CuratorEngine
    "CuratorEngine",
    "CuratorConfig",
    "PlaylistState",
    "EnergyCurveTemplates",
    # Narrative
    "NarrativeAdapter",
    "NarrativeGenerator",
    "PlaylistTheme",
    "generate_playlist_narrative",
    "explain_playlist_theme",
    "generate_song_explanation",
    "detect_playlist_theme",
]
