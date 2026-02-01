"""
Curator Engine Types v1.0 - Enriched Data Model
Phase 2: Dynamic DJ Graph

MODULE 1: Enhanced Song representation with:
- Semantic Layer (lyrical_valence, lyrical_contrast)
- Narrative Potential (build_up_potential)
- Texture Tags (ORGANIC, SYNTHETIC, DISTORTED, ATMOSPHERIC)
- Camelot Wheel integration for harmonic mixing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List, Any

# =============================================================================
# TEXTURE TYPES
# Simplified audio texture for DJ-style transitions
# =============================================================================

class TextureType(Enum):
    """Audio texture categories for smooth transitions."""
    ORGANIC = "organic"           # Acoustic, piano, strings, live instruments
    SYNTHETIC = "synthetic"       # Electronic, synth, EDM, lofi
    DISTORTED = "distorted"       # Rock, metal, heavily processed
    ATMOSPHERIC = "atmospheric"   # Ambient, drone, soundscape
    HYBRID = "hybrid"             # Mix of textures - good for bridging


# =============================================================================
# CAMELOT WHEEL
# Standard DJ harmonic mixing system
# =============================================================================

# Key (0-11) to Camelot mapping
# Minor keys = A, Major keys = B
CAMELOT_MINOR = {
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

CAMELOT_MAJOR = {
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
        return "??"  # Unknown key
    
    key_int = int(key) % 12
    
    if mode == 1:  # Major
        return CAMELOT_MAJOR.get(key_int, "??")
    else:  # Minor or unknown
        return CAMELOT_MINOR.get(key_int, "??")


def camelot_distance(code1: str, code2: str) -> int:
    """
    Calculate "distance" on the Camelot wheel.
    
    Returns:
        0 = exact match or relative major/minor
        1 = adjacent (perfect for mixing)
        2 = energy boost jump
        3+ = clash (avoid or use intentionally)
    """
    if code1 == "??" or code2 == "??":
        return 2  # Unknown = neutral distance
    
    # Parse codes
    num1, letter1 = int(code1[:-1]), code1[-1]
    num2, letter2 = int(code2[:-1]), code2[-1]
    
    # Same key & mode = perfect
    if code1 == code2:
        return 0
    
    # Relative major/minor (same number, different letter)
    if num1 == num2 and letter1 != letter2:
        return 0
    
    # Adjacent on wheel (±1)
    if letter1 == letter2:
        diff = abs(num1 - num2)
        # Wheel wraps at 12
        diff = min(diff, 12 - diff)
        if diff == 1:
            return 1
        elif diff == 2:
            return 2  # Energy boost
        else:
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
# TEXTURE DETECTION HEURISTICS
# =============================================================================

ORGANIC_KEYWORDS = {
    "acoustic", "piano", "strings", "orchestra", "classical",
    "folk", "unplugged", "live", "jazz", "blues", "soul",
    "flamenco", "guitar", "violin", "cello", "chamber"
}

SYNTHETIC_KEYWORDS = {
    "electronic", "edm", "house", "techno", "trance", "synth",
    "lofi", "lo-fi", "chillwave", "synthwave", "retrowave",
    "dubstep", "dnb", "drum and bass", "electro", "future",
    "hyperpop", "trap", "hardstyle"
}

DISTORTED_KEYWORDS = {
    "rock", "metal", "punk", "grunge", "hardcore", "heavy",
    "industrial", "noise", "shoegaze", "post-rock", "stoner",
    "doom", "death", "black metal", "thrash", "nu-metal"
}

ATMOSPHERIC_KEYWORDS = {
    "ambient", "drone", "soundscape", "meditation", "new age",
    "dark ambient", "space", "ethereal", "cinematic", "film score",
    "atmospheric", "minimalist"
}


def detect_texture(genre: Optional[str], acousticness: float = 50.0) -> TextureType:
    """
    Detect texture type from genre and acousticness.
    
    Returns TextureType enum.
    """
    if genre is None:
        # Fallback to acousticness
        if acousticness > 70:
            return TextureType.ORGANIC
        elif acousticness < 30:
            return TextureType.SYNTHETIC
        return TextureType.HYBRID
    
    genre_lower = genre.lower()
    
    # Check each texture category
    for keyword in DISTORTED_KEYWORDS:
        if keyword in genre_lower:
            return TextureType.DISTORTED
    
    for keyword in ATMOSPHERIC_KEYWORDS:
        if keyword in genre_lower:
            return TextureType.ATMOSPHERIC
    
    for keyword in ORGANIC_KEYWORDS:
        if keyword in genre_lower:
            return TextureType.ORGANIC
    
    for keyword in SYNTHETIC_KEYWORDS:
        if keyword in genre_lower:
            return TextureType.SYNTHETIC
    
    # Fallback to acousticness
    if acousticness > 65:
        return TextureType.ORGANIC
    elif acousticness < 35:
        return TextureType.SYNTHETIC
    
    return TextureType.HYBRID


# =============================================================================
# TEXTURE TRANSITION SCORING
# =============================================================================

# Transition smoothness matrix
# 1.0 = perfect, 0.0 = clash
TEXTURE_TRANSITION_SCORES = {
    (TextureType.ORGANIC, TextureType.ORGANIC): 1.0,
    (TextureType.ORGANIC, TextureType.HYBRID): 0.8,
    (TextureType.ORGANIC, TextureType.ATMOSPHERIC): 0.7,
    (TextureType.ORGANIC, TextureType.SYNTHETIC): 0.3,  # Jarring
    (TextureType.ORGANIC, TextureType.DISTORTED): 0.2,  # Very jarring
    
    (TextureType.SYNTHETIC, TextureType.SYNTHETIC): 1.0,
    (TextureType.SYNTHETIC, TextureType.HYBRID): 0.8,
    (TextureType.SYNTHETIC, TextureType.DISTORTED): 0.6,  # Can work
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


# =============================================================================
# ENRICHED SONG (CURATOR TRACK)
# =============================================================================

@dataclass
class CuratorTrack:
    """
    Enriched Song representation for Curator Engine.
    
    Extends raw Song dict with:
    - Semantic layer (lyrical analysis)
    - Narrative potential (build-up detection)
    - Texture classification
    - Camelot harmonic code
    """
    
    # === IDENTITY ===
    song_id: int
    title: str
    artist: str
    genre: Optional[str] = None
    
    # === CORE AUDIO FEATURES (from MoodEngine) ===
    valence_score: float = 50.0      # Audio/emotional valence
    arousal_score: float = 50.0      # Energy/arousal
    tempo: float = 120.0
    energy: float = 50.0
    danceability: float = 50.0
    acousticness: float = 50.0
    loudness: float = -10.0
    
    # === MOOD (from MoodEngine) ===
    mood: str = "happy"
    mood_confidence: float = 0.5
    intensity: int = 2  # 1=low, 2=medium, 3=high
    
    # === HARMONIC (for mixing) ===
    key: Optional[int] = None        # 0-11
    mode: Optional[int] = None       # 0=minor, 1=major
    
    # === SEMANTIC LAYER (NEW) ===
    lyrical_valence: Optional[float] = None  # 0-100, sentiment of lyrics
    lyrical_contrast: bool = False           # True if audio vs lyric contrast
    
    # === NARRATIVE POTENTIAL (NEW) ===
    build_up_potential: float = 0.0  # 0.0-1.0, probability of energy explosion
    energy_buildup: Optional[float] = None
    tension_level: Optional[float] = None
    
    # === TEXTURE (NEW) ===
    texture_type: TextureType = field(default=TextureType.HYBRID)
    
    # === CONTEXT SCORES (from MoodEngine) ===
    morning_score: Optional[float] = None
    evening_score: Optional[float] = None
    workout_score: Optional[float] = None
    focus_score: Optional[float] = None
    relax_score: Optional[float] = None
    party_score: Optional[float] = None
    
    # === CURATOR STATE (dynamic) ===
    skip_count: int = 0              # How many times user skipped this
    play_count: int = 0              # How many times user played this
    last_played_position: Optional[int] = None  # Position in last playlist
    
    def __post_init__(self):
        """Auto-calculate derived fields."""
        # Calculate lyrical contrast
        if self.lyrical_valence is not None:
            contrast = abs(self.valence_score - self.lyrical_valence)
            self.lyrical_contrast = contrast > 30
        
        # Auto-detect texture if not set
        if self.texture_type == TextureType.HYBRID:
            self.texture_type = detect_texture(self.genre, self.acousticness)
        
        # Estimate build-up potential from features
        if self.build_up_potential == 0.0:
            self._estimate_build_up_potential()
    
    def _estimate_build_up_potential(self):
        """
        Estimate build-up potential from audio features.
        High energy_buildup + high tension + moderate start energy = likely explosion
        """
        if self.energy_buildup is not None and self.tension_level is not None:
            # High buildup + high tension = likely explosion
            buildup_norm = (self.energy_buildup or 50) / 100.0
            tension_norm = (self.tension_level or 50) / 100.0
            
            # Moderate energy = more room to grow
            energy_headroom = max(0, 100 - self.energy) / 100.0
            
            self.build_up_potential = (
                0.4 * buildup_norm + 
                0.3 * tension_norm + 
                0.3 * energy_headroom
            )
            self.build_up_potential = min(1.0, self.build_up_potential)
    
    @property
    def camelot_code(self) -> str:
        """Get Camelot wheel code for harmonic mixing."""
        return key_mode_to_camelot(self.key, self.mode)
    
    @classmethod
    def from_song_dict(cls, song: Dict[str, Any]) -> "CuratorTrack":
        """
        Create CuratorTrack from raw Song dict (database row).
        """
        def _to_float(val, default=None):
            if val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default
        
        def _to_int(val, default=None):
            if val is None:
                return default
            try:
                return int(val)
            except (ValueError, TypeError):
                return default
        
        # Handle different column naming conventions
        title = song.get("title") or song.get("song_name") or "Unknown"
        song_id = _to_int(song.get("id") or song.get("song_id"), 0)
        
        return cls(
            song_id=song_id,
            title=title,
            artist=song.get("artist") or "Unknown",
            genre=song.get("genre"),
            
            # Core audio
            valence_score=_to_float(song.get("valence_score") or song.get("valence"), 50.0),
            arousal_score=_to_float(song.get("arousal_score") or song.get("energy"), 50.0),
            tempo=_to_float(song.get("tempo"), 120.0),
            energy=_to_float(song.get("energy"), 50.0),
            danceability=_to_float(song.get("danceability"), 50.0),
            acousticness=_to_float(song.get("acousticness"), 50.0),
            loudness=_to_float(song.get("loudness"), -10.0),
            
            # Mood
            mood=song.get("mood") or "happy",
            mood_confidence=_to_float(song.get("mood_confidence"), 0.5),
            intensity=_to_int(song.get("intensity"), 2),
            
            # Harmonic
            key=_to_int(song.get("key")),
            mode=_to_int(song.get("mode")),
            
            # Narrative
            energy_buildup=_to_float(song.get("energy_buildup")),
            tension_level=_to_float(song.get("tension_level")),
            
            # Context
            morning_score=_to_float(song.get("morning_score")),
            evening_score=_to_float(song.get("evening_score")),
            workout_score=_to_float(song.get("workout_score")),
            focus_score=_to_float(song.get("focus_score")),
            relax_score=_to_float(song.get("relax_score")),
            party_score=_to_float(song.get("party_score")),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "song_id": self.song_id,
            "title": self.title,
            "artist": self.artist,
            "genre": self.genre,
            "valence_score": self.valence_score,
            "arousal_score": self.arousal_score,
            "tempo": self.tempo,
            "energy": self.energy,
            "mood": self.mood,
            "mood_confidence": self.mood_confidence,
            "intensity": self.intensity,
            "camelot_code": self.camelot_code,
            "texture_type": self.texture_type.value,
            "lyrical_contrast": self.lyrical_contrast,
            "build_up_potential": self.build_up_potential,
        }


# =============================================================================
# PLAYLIST STATE (for Dynamic Re-routing)
# =============================================================================

@dataclass
class PlaylistState:
    """
    Dynamic state for re-routing decisions.
    Tracks user behavior within a session.
    """
    
    # Current playlist
    tracks: List[CuratorTrack] = field(default_factory=list)
    current_index: int = 0
    
    # User preference signals (session-level)
    texture_preferences: Dict[TextureType, float] = field(default_factory=dict)
    recent_skips: List[int] = field(default_factory=list)  # song_ids
    recent_plays: List[int] = field(default_factory=list)  # song_ids
    
    # Target curve
    energy_curve: List[float] = field(default_factory=list)
    target_mood: str = "happy"
    
    def __post_init__(self):
        """Initialize texture preferences with neutral values."""
        if not self.texture_preferences:
            for t in TextureType:
                self.texture_preferences[t] = 1.0
    
    def record_skip(self, track: CuratorTrack):
        """Record a skip event - user doesn't want this."""
        self.recent_skips.append(track.song_id)
        
        # Penalize this texture
        current_pref = self.texture_preferences.get(track.texture_type, 1.0)
        self.texture_preferences[track.texture_type] = max(0.3, current_pref - 0.2)
        
        # Keep only last 10 skips
        self.recent_skips = self.recent_skips[-10:]
    
    def record_play(self, track: CuratorTrack):
        """Record a full play - user liked this."""
        self.recent_plays.append(track.song_id)
        
        # Boost this texture
        current_pref = self.texture_preferences.get(track.texture_type, 1.0)
        self.texture_preferences[track.texture_type] = min(1.5, current_pref + 0.1)
        
        # Keep only last 20 plays
        self.recent_plays = self.recent_plays[-20:]
    
    def get_texture_multiplier(self, texture: TextureType) -> float:
        """Get preference multiplier for a texture type."""
        return self.texture_preferences.get(texture, 1.0)
    
    @property
    def current_track(self) -> Optional[CuratorTrack]:
        """Get current track or None."""
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None
    
    @property
    def remaining_curve(self) -> List[float]:
        """Get remaining energy targets."""
        if self.current_index < len(self.energy_curve):
            return self.energy_curve[self.current_index:]
        return []
