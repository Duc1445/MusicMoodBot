"""
Schema Module v2.0 - Phase 2 Data Model
========================================

This module contains the core data models for the Music Chatbot Backend.
It defines the Song dataclass with both legacy MIR features and new Phase 2 semantic fields.

Architecture Decision:
    Separated from MoodEngine to maintain Single Responsibility Principle.
    All other modules import from here, preventing circular dependencies.

Version History:
    v1.0: Basic Song dict type alias
    v2.0: Full dataclass with Phase 2 fields (lyrical_valence, texture, build_up, camelot)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union

# =============================================================================
# TYPE ALIASES
# =============================================================================

Number = float
SongDict = Dict[str, Any]  # Legacy compatibility

# =============================================================================
# ENUMS
# =============================================================================


class Mood(str, Enum):
    """
    Primary mood categories derived from VA (Valence-Arousal) space.
    
    Mapping to Russell's Circumplex Model:
        - ENERGETIC: High Valence, High Arousal (excitement, elation)
        - HAPPY: High Valence, Low Arousal (contentment, serenity)
        - SAD: Low Valence, Low Arousal (depression, boredom)
        - STRESS: Low Valence, High Arousal (tension, nervousness)
        - ANGRY: Very Low Valence, Very High Arousal (rage, frustration)
    """
    ENERGETIC = "energetic"
    HAPPY = "happy"
    SAD = "sad"
    STRESS = "stress"
    ANGRY = "angry"


class TextureType(str, Enum):
    """
    Audio texture categories for DJ-style transitions.
    
    Used by CuratorEngine to ensure smooth texture flow between tracks.
    Jarring texture transitions (e.g., ORGANIC → DISTORTED) receive penalties
    unless there's a significant energy jump to justify the shift.
    
    Categories:
        ORGANIC: Acoustic, piano, strings, live instruments
        SYNTHETIC: Electronic, synth, EDM, lo-fi
        DISTORTED: Rock, metal, heavily processed guitars
        ATMOSPHERIC: Ambient, drone, soundscape, ethereal
        HYBRID: Mix of textures - serves as a bridge between categories
    """
    ORGANIC = "organic"
    SYNTHETIC = "synthetic"
    DISTORTED = "distorted"
    ATMOSPHERIC = "atmospheric"
    HYBRID = "hybrid"


class Intensity(str, Enum):
    """Intensity levels for mood classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# =============================================================================
# MOOD CONSTANTS
# =============================================================================

# List of mood strings for backward compatibility
MOODS: List[str] = [m.value for m in Mood]

# Vietnamese mood labels
MOODS_VI: Dict[str, str] = {
    "energetic": "Năng lượng",
    "happy": "Vui",
    "sad": "Buồn",
    "stress": "Suy tư",
    "angry": "Mạnh mẽ",
}

# Mood descriptions
MOOD_DESCRIPTIONS: Dict[str, str] = {
    "energetic": "đầy năng lượng, sôi động",
    "happy": "vui vẻ, tích cực",
    "sad": "buồn, trầm lắng",
    "stress": "căng thẳng, lo lắng",
    "angry": "mạnh mẽ, dữ dội",
}

# =============================================================================
# CAMELOT WHEEL CONSTANTS
# =============================================================================

# Key (0-11) to Camelot mapping - Minor keys
CAMELOT_MINOR: Dict[int, str] = {
    0: "5A",   # C minor
    1: "12A",  # C# minor
    2: "7A",   # D minor
    3: "2A",   # D# minor
    4: "9A",   # E minor
    5: "4A",   # F minor
    6: "11A",  # F# minor
    7: "6A",   # G minor
    8: "1A",   # G# minor
    9: "8A",   # A minor
    10: "3A",  # A# minor
    11: "10A", # B minor
}

# Key (0-11) to Camelot mapping - Major keys
CAMELOT_MAJOR: Dict[int, str] = {
    0: "8B",   # C major
    1: "3B",   # C# major
    2: "10B",  # D major
    3: "5B",   # D# major
    4: "12B",  # E major
    5: "7B",   # F major
    6: "2B",   # F# major
    7: "9B",   # G major
    8: "4B",   # G# major
    9: "11B",  # A major
    10: "6B",  # A# major
    11: "1B",  # B major
}

# Camelot valence bias for minor keys
CAMELOT_VALENCE_BIAS: Dict[int, int] = {
    0: -4,   # C minor (5A) - neutral minor
    1: -2,   # C# minor (12A)
    2: -3,   # D minor (7A)
    3: -5,   # D# minor (2A) - darker
    4: +2,   # E minor (9A) - brighter minor
    5: -1,   # F minor (4A)
    6: -6,   # F# minor (11A) - very dark
    7: +3,   # G minor (6A) - emotional but not dark
    8: -4,   # G# minor (1A) - dark
    9: +4,   # A minor (8A) - common, bright minor
    10: -3,  # A# minor (3A)
    11: +1,  # B minor (10A)
}

# Camelot valence boost for major keys
CAMELOT_MAJOR_BOOST: Dict[int, int] = {
    0: +6,   # C major (8B) - very bright
    1: +4,   # C# major (3B)
    2: +5,   # D major (10B) - bright
    3: +3,   # D# major (5B)
    4: +7,   # E major (12B) - very bright
    5: +4,   # F major (7B)
    6: +2,   # F# major (2B)
    7: +8,   # G major (9B) - extremely bright
    8: +3,   # G# major (4B)
    9: +5,   # A major (11B) - bright
    10: +4,  # A# major (6B)
    11: +6,  # B major (1B)
}

# =============================================================================
# ORCHESTRAL GENRES (v5.2 Context-Aware Acoustic)
# =============================================================================

ORCHESTRAL_GENRES: set = {
    "classical", "soundtrack", "orchestral", "opera", "symphony",
    "film score", "cinematic", "epic", "trailer", "game soundtrack",
    "neo-classical", "chamber", "baroque", "romantic", "contemporary classical",
    "flamenco", "acoustic rock", "unplugged", "live"
}


# =============================================================================
# SONG DATACLASS
# =============================================================================

@dataclass
class Song:
    """
    Enhanced Song representation for Phase 2 architecture.
    
    Combines:
    - Core MIR features (from Spotify/TuneBat analysis)
    - Phase 2 Semantic fields (lyrical sentiment, texture, narrative potential)
    - Computed metrics (output of MoodEngine)
    
    This dataclass serves as the canonical data model throughout the pipeline:
    1. Database → Song (via from_dict)
    2. Song → MoodEngine.predict() → Song with computed fields
    3. Song → CuratorEngine → Playlist ordering
    4. Song → NarrativeAdapter → Human-readable explanation
    
    Attributes:
        Core Identity:
            song_id: Unique identifier
            title: Track title
            artist: Artist name
            genre: Genre string (may contain multiple genres separated by +, /, etc.)
        
        Core MIR Features (0-100 scale unless noted):
            tempo: Beats per minute (float, typically 60-200)
            energy: Perceived energy level
            valence: Musical positiveness/happiness
            arousal: Computed arousal score (if already processed)
            danceability: How suitable for dancing
            loudness: Loudness in dB (typically -60 to 0)
            mode: Musical mode (0=minor, 1=major)
            key: Pitch class (0-11, C=0, C#=1, ..., B=11)
            acousticness: How acoustic vs electronic
        
        Phase 2 Semantic Fields:
            lyrical_valence: Sentiment of lyrics (0-100, nullable)
            texture_type: Audio texture classification
            build_up_potential: Probability of energy explosion (0.0-1.0)
            harmonic_camelot: Camelot wheel code (e.g., "8B", "5A")
        
        Computed Metrics (Output of MoodEngine):
            normalized_loudness: Loudness normalized to 0-100
            effective_danceability: Kinetic-aware dance score
            mood_label: Predicted mood category
            mood_confidence: Confidence of mood prediction
            valence_score: Computed valence in VA space
            arousal_score: Computed arousal in VA space
            intensity: Intensity level (1-3)
    """
    
    # === IDENTITY ===
    song_id: int = 0
    title: str = "Unknown"
    artist: str = "Unknown"
    genre: Optional[str] = None
    
    # === CORE MIR FEATURES ===
    tempo: float = 120.0
    energy: float = 50.0
    valence: float = 50.0
    arousal: Optional[float] = None  # May be computed or provided
    danceability: float = 50.0
    loudness: float = -10.0  # dB
    mode: Optional[int] = None  # 0=minor, 1=major
    key: Optional[int] = None  # 0-11
    acousticness: float = 50.0
    
    # === ADDITIONAL MIR FEATURES ===
    happiness: Optional[float] = None  # TuneBat happiness (separate from valence)
    liveness: float = 10.0
    speechiness: float = 0.0
    instrumentalness: float = 0.0
    
    # === ADVANCED FEATURES ===
    tension_level: Optional[float] = None
    groove_factor: Optional[float] = None
    energy_buildup: Optional[float] = None
    rhythmic_complexity: Optional[float] = None
    harmonic_complexity: Optional[float] = None
    melodic_brightness: Optional[float] = None
    atmospheric_depth: Optional[float] = None
    emotional_depth: Optional[float] = None
    emotional_volatility: Optional[float] = None
    mood_stability: Optional[float] = None
    nostalgia_factor: Optional[float] = None
    release_satisfaction: Optional[float] = None
    
    # === PHASE 2 SEMANTIC FIELDS ===
    lyrical_valence: Optional[float] = None  # 0-100, sentiment of lyrics
    texture_type: TextureType = field(default=TextureType.HYBRID)
    build_up_potential: float = 0.0  # 0.0-1.0
    harmonic_camelot: Optional[str] = None  # e.g., "8B", "5A"
    
    # === COMPUTED METRICS (Output of MoodEngine) ===
    normalized_loudness: Optional[float] = None  # 0-100
    effective_danceability: Optional[float] = None  # kinetic-aware
    mood_label: Optional[str] = None
    mood_confidence: float = 0.5
    valence_score: Optional[float] = None  # Computed VA valence
    arousal_score: Optional[float] = None  # Computed VA arousal
    intensity: int = 2  # 1=low, 2=medium, 3=high
    
    # === CONTEXT SCORES ===
    morning_score: Optional[float] = None
    evening_score: Optional[float] = None
    workout_score: Optional[float] = None
    focus_score: Optional[float] = None
    relax_score: Optional[float] = None
    party_score: Optional[float] = None
    
    # === CURATOR STATE (dynamic) ===
    skip_count: int = 0
    play_count: int = 0
    
    def __post_init__(self):
        """Auto-calculate derived fields."""
        # Calculate Camelot code if not provided
        if self.harmonic_camelot is None and self.key is not None:
            self.harmonic_camelot = self._compute_camelot()
        
        # Detect texture if still HYBRID and genre is available
        if self.texture_type == TextureType.HYBRID and self.genre:
            self.texture_type = self._detect_texture()
        
        # Estimate build_up_potential if not set
        if self.build_up_potential == 0.0:
            self._estimate_build_up()
        
        # Calculate lyrical contrast flag
        self._lyrical_contrast = False
        if self.lyrical_valence is not None and self.valence is not None:
            self._lyrical_contrast = abs(self.valence - self.lyrical_valence) > 30
    
    def _compute_camelot(self) -> str:
        """Convert key/mode to Camelot notation."""
        if self.key is None:
            return "??"
        key_int = int(self.key) % 12
        if self.mode == 1:  # Major
            return CAMELOT_MAJOR.get(key_int, "??")
        else:  # Minor or unknown
            return CAMELOT_MINOR.get(key_int, "??")
    
    def _detect_texture(self) -> TextureType:
        """Detect texture type from genre and acousticness."""
        if not self.genre:
            return TextureType.HYBRID
        
        genre_lower = self.genre.lower()
        
        # Check keywords
        distorted_kw = {"rock", "metal", "punk", "grunge", "hardcore", "heavy", "industrial", "noise"}
        atmospheric_kw = {"ambient", "drone", "soundscape", "meditation", "new age", "ethereal", "cinematic"}
        organic_kw = {"acoustic", "piano", "strings", "orchestra", "classical", "folk", "jazz", "blues"}
        synthetic_kw = {"electronic", "edm", "house", "techno", "trance", "synth", "lofi", "dubstep"}
        
        for kw in distorted_kw:
            if kw in genre_lower:
                return TextureType.DISTORTED
        for kw in atmospheric_kw:
            if kw in genre_lower:
                return TextureType.ATMOSPHERIC
        for kw in organic_kw:
            if kw in genre_lower:
                return TextureType.ORGANIC
        for kw in synthetic_kw:
            if kw in genre_lower:
                return TextureType.SYNTHETIC
        
        # Fallback to acousticness
        if self.acousticness > 65:
            return TextureType.ORGANIC
        elif self.acousticness < 35:
            return TextureType.SYNTHETIC
        
        return TextureType.HYBRID
    
    def _estimate_build_up(self) -> None:
        """Estimate build-up potential from audio features."""
        if self.energy_buildup is not None and self.tension_level is not None:
            buildup_norm = (self.energy_buildup or 50) / 100.0
            tension_norm = (self.tension_level or 50) / 100.0
            energy_headroom = max(0, 100 - self.energy) / 100.0
            
            self.build_up_potential = (
                0.4 * buildup_norm +
                0.3 * tension_norm +
                0.3 * energy_headroom
            )
            self.build_up_potential = min(1.0, self.build_up_potential)
    
    @property
    def lyrical_contrast(self) -> bool:
        """True if audio valence contrasts with lyrical sentiment."""
        return getattr(self, '_lyrical_contrast', False)
    
    @property
    def camelot_code(self) -> str:
        """Alias for harmonic_camelot."""
        return self.harmonic_camelot or "??"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Song":
        """
        Create Song from raw dict (database row or API response).
        
        Handles various naming conventions:
        - song_id vs id
        - song_name vs title
        - Spotify 0-1 scale vs TuneBat 0-100 scale
        """
        def _to_float(val: Any, default: Optional[float] = None) -> Optional[float]:
            if val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default
        
        def _to_int(val: Any, default: Optional[int] = None) -> Optional[int]:
            if val is None:
                return default
            try:
                return int(val)
            except (ValueError, TypeError):
                return default
        
        def _coerce_0_100(val: Any, default: float = 50.0) -> float:
            """Convert 0-1 scale to 0-100 if needed."""
            if val is None:
                return default
            try:
                v = float(val)
                if 0.0 <= v <= 1.0:
                    return v * 100.0
                return max(0.0, min(100.0, v))
            except (ValueError, TypeError):
                return default
        
        # Handle different column naming
        song_id = _to_int(data.get("id") or data.get("song_id"), 0)
        title = data.get("title") or data.get("song_name") or "Unknown"
        
        # Parse texture type
        texture_raw = data.get("texture_type")
        texture = TextureType.HYBRID
        if isinstance(texture_raw, TextureType):
            texture = texture_raw
        elif isinstance(texture_raw, str):
            try:
                texture = TextureType(texture_raw.lower())
            except ValueError:
                texture = TextureType.HYBRID
        
        return cls(
            song_id=song_id,
            title=title,
            artist=data.get("artist") or "Unknown",
            genre=data.get("genre"),
            
            # Core MIR
            tempo=_to_float(data.get("tempo"), 120.0),
            energy=_coerce_0_100(data.get("energy"), 50.0),
            valence=_coerce_0_100(data.get("valence"), 50.0),
            arousal=_to_float(data.get("arousal")),
            danceability=_coerce_0_100(data.get("danceability"), 50.0),
            loudness=_to_float(data.get("loudness"), -10.0),
            mode=_to_int(data.get("mode")),
            key=_to_int(data.get("key")),
            acousticness=_coerce_0_100(data.get("acousticness"), 50.0),
            
            # Additional MIR
            happiness=_to_float(data.get("happiness")),
            liveness=_coerce_0_100(data.get("liveness"), 10.0),
            
            # Advanced features
            tension_level=_to_float(data.get("tension_level")),
            groove_factor=_to_float(data.get("groove_factor")),
            energy_buildup=_to_float(data.get("energy_buildup")),
            rhythmic_complexity=_to_float(data.get("rhythmic_complexity")),
            harmonic_complexity=_to_float(data.get("harmonic_complexity")),
            melodic_brightness=_to_float(data.get("melodic_brightness")),
            atmospheric_depth=_to_float(data.get("atmospheric_depth")),
            emotional_depth=_to_float(data.get("emotional_depth")),
            emotional_volatility=_to_float(data.get("emotional_volatility")),
            mood_stability=_to_float(data.get("mood_stability")),
            nostalgia_factor=_to_float(data.get("nostalgia_factor")),
            release_satisfaction=_to_float(data.get("release_satisfaction")),
            
            # Phase 2
            lyrical_valence=_to_float(data.get("lyrical_valence")),
            texture_type=texture,
            build_up_potential=_to_float(data.get("build_up_potential"), 0.0),
            harmonic_camelot=data.get("harmonic_camelot"),
            
            # Computed (may be pre-computed)
            normalized_loudness=_to_float(data.get("normalized_loudness")),
            effective_danceability=_to_float(data.get("effective_danceability")),
            mood_label=data.get("mood_label") or data.get("mood"),
            mood_confidence=_to_float(data.get("mood_confidence"), 0.5),
            valence_score=_to_float(data.get("valence_score")),
            arousal_score=_to_float(data.get("arousal_score")),
            intensity=_to_int(data.get("intensity"), 2),
            
            # Context
            morning_score=_to_float(data.get("morning_score")),
            evening_score=_to_float(data.get("evening_score")),
            workout_score=_to_float(data.get("workout_score")),
            focus_score=_to_float(data.get("focus_score")),
            relax_score=_to_float(data.get("relax_score")),
            party_score=_to_float(data.get("party_score")),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization or database storage."""
        return {
            "song_id": self.song_id,
            "title": self.title,
            "artist": self.artist,
            "genre": self.genre,
            
            # Core MIR
            "tempo": self.tempo,
            "energy": self.energy,
            "valence": self.valence,
            "danceability": self.danceability,
            "loudness": self.loudness,
            "mode": self.mode,
            "key": self.key,
            "acousticness": self.acousticness,
            
            # Phase 2
            "lyrical_valence": self.lyrical_valence,
            "texture_type": self.texture_type.value,
            "build_up_potential": self.build_up_potential,
            "harmonic_camelot": self.harmonic_camelot,
            
            # Computed
            "normalized_loudness": self.normalized_loudness,
            "effective_danceability": self.effective_danceability,
            "mood_label": self.mood_label,
            "mood_confidence": self.mood_confidence,
            "valence_score": self.valence_score,
            "arousal_score": self.arousal_score,
            "intensity": self.intensity,
            "lyrical_contrast": self.lyrical_contrast,
        }
    
    def to_legacy_dict(self) -> Dict[str, object]:
        """Convert to legacy Song dict format for backward compatibility."""
        result: Dict[str, object] = {
            "id": self.song_id,
            "title": self.title,
            "artist": self.artist,
            "genre": self.genre,
            "tempo": self.tempo,
            "energy": self.energy,
            "valence": self.valence,
            "happiness": self.happiness,
            "danceability": self.danceability,
            "loudness": self.loudness,
            "mode": self.mode,
            "key": self.key,
            "acousticness": self.acousticness,
            "liveness": self.liveness,
        }
        
        # Add optional fields if set
        for field_name in [
            "tension_level", "groove_factor", "energy_buildup", 
            "rhythmic_complexity", "harmonic_complexity", "melodic_brightness",
            "atmospheric_depth", "emotional_depth", "emotional_volatility",
            "mood_stability", "nostalgia_factor", "release_satisfaction",
            "morning_score", "evening_score", "workout_score",
            "focus_score", "relax_score", "party_score"
        ]:
            val = getattr(self, field_name, None)
            if val is not None:
                result[field_name] = val
        
        return result


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def key_mode_to_camelot(key: Optional[int], mode: Optional[int]) -> str:
    """
    Convert Spotify key/mode to Camelot notation.
    
    Args:
        key: 0-11 (C=0, C#=1, ... B=11)
        mode: 0=minor, 1=major
    
    Returns:
        Camelot code like "8A" or "5B"
    """
    if key is None:
        return "??"
    key_int = int(key) % 12
    if mode == 1:
        return CAMELOT_MAJOR.get(key_int, "??")
    return CAMELOT_MINOR.get(key_int, "??")


def camelot_distance(code1: str, code2: str) -> int:
    """
    Calculate "distance" on the Camelot wheel.
    
    Returns:
        0 = exact match or relative major/minor (perfect mix)
        1 = adjacent on wheel (great for mixing)
        2 = energy boost jump (+2 on wheel)
        3+ = clash (avoid or use intentionally for dramatic effect)
    """
    if code1 == "??" or code2 == "??":
        return 2  # Unknown = neutral distance
    
    try:
        num1, letter1 = int(code1[:-1]), code1[-1]
        num2, letter2 = int(code2[:-1]), code2[-1]
    except (ValueError, IndexError):
        return 2
    
    # Same key & mode = perfect
    if code1 == code2:
        return 0
    
    # Relative major/minor (same number, different letter)
    if num1 == num2 and letter1 != letter2:
        return 0
    
    # Adjacent on wheel (±1)
    if letter1 == letter2:
        diff = abs(num1 - num2)
        diff = min(diff, 12 - diff)  # Wheel wraps at 12
        return diff
    
    # Cross-mode jump
    diff = abs(num1 - num2)
    diff = min(diff, 12 - diff)
    return diff + 1


def is_harmonic_compatible(code1: str, code2: str, allow_boost: bool = False) -> bool:
    """
    Check if two Camelot codes are harmonically compatible.
    
    Args:
        code1: Current track Camelot code
        code2: Next track Camelot code
        allow_boost: If True, allow +2 "energy boost" transitions
    
    Returns:
        True if transition is smooth/acceptable
    """
    dist = camelot_distance(code1, code2)
    if allow_boost:
        return dist <= 2
    return dist <= 1


# =============================================================================
# TEXTURE UTILITIES
# =============================================================================

# Transition smoothness matrix (1.0 = perfect, 0.0 = clash)
TEXTURE_TRANSITION_SCORES: Dict[tuple, float] = {
    (TextureType.ORGANIC, TextureType.ORGANIC): 1.0,
    (TextureType.ORGANIC, TextureType.HYBRID): 0.8,
    (TextureType.ORGANIC, TextureType.ATMOSPHERIC): 0.7,
    (TextureType.ORGANIC, TextureType.SYNTHETIC): 0.3,
    (TextureType.ORGANIC, TextureType.DISTORTED): 0.2,
    
    (TextureType.SYNTHETIC, TextureType.SYNTHETIC): 1.0,
    (TextureType.SYNTHETIC, TextureType.HYBRID): 0.8,
    (TextureType.SYNTHETIC, TextureType.DISTORTED): 0.6,
    (TextureType.SYNTHETIC, TextureType.ATMOSPHERIC): 0.5,
    (TextureType.SYNTHETIC, TextureType.ORGANIC): 0.3,
    
    (TextureType.DISTORTED, TextureType.DISTORTED): 1.0,
    (TextureType.DISTORTED, TextureType.SYNTHETIC): 0.6,
    (TextureType.DISTORTED, TextureType.HYBRID): 0.7,
    (TextureType.DISTORTED, TextureType.ATMOSPHERIC): 0.4,
    (TextureType.DISTORTED, TextureType.ORGANIC): 0.2,
    
    (TextureType.ATMOSPHERIC, TextureType.ATMOSPHERIC): 1.0,
    (TextureType.ATMOSPHERIC, TextureType.ORGANIC): 0.7,
    (TextureType.ATMOSPHERIC, TextureType.HYBRID): 0.8,
    (TextureType.ATMOSPHERIC, TextureType.SYNTHETIC): 0.5,
    (TextureType.ATMOSPHERIC, TextureType.DISTORTED): 0.3,
    
    (TextureType.HYBRID, TextureType.HYBRID): 1.0,
    (TextureType.HYBRID, TextureType.ORGANIC): 0.8,
    (TextureType.HYBRID, TextureType.SYNTHETIC): 0.8,
    (TextureType.HYBRID, TextureType.ATMOSPHERIC): 0.8,
    (TextureType.HYBRID, TextureType.DISTORTED): 0.7,
}


def texture_transition_score(from_texture: TextureType, to_texture: TextureType) -> float:
    """Get transition smoothness score between textures."""
    return TEXTURE_TRANSITION_SCORES.get((from_texture, to_texture), 0.5)
