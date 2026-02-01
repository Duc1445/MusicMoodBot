"""
Shared type definitions for MusicMoodBot
"""

from typing import Dict, List, Optional, TypedDict, Any
from dataclasses import dataclass
from enum import Enum

# ================== ENUMS ==================
class MoodType(str, Enum):
    ENERGETIC = "energetic"
    HAPPY = "happy"
    SAD = "sad"
    STRESS = "stress"
    ANGRY = "angry"

class MoodTypeVI(str, Enum):
    VUI = "Vui"
    BUON = "Buồn"
    SUY_TU = "Suy tư"
    CHILL = "Chill"
    NANG_LUONG = "Năng lượng"

class IntensityType(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class IntensityTypeVI(str, Enum):
    NHE = "Nhẹ"
    VUA = "Vừa"
    MANH = "Mạnh"

# ================== TYPED DICTS ==================
class SongDict(TypedDict, total=False):
    id: int
    title: str
    artist: str
    genre: str
    energy: float
    happiness: float
    valence: float
    danceability: float
    acousticness: float
    tempo: float
    loudness: float
    mood: str
    intensity: int
    play_count: int
    skip_count: int
    like_count: int
    created_at: str
    updated_at: str

class RecommendationDict(TypedDict, total=False):
    song: SongDict
    score: float
    reason: str
    mood_match: float
    energy_match: float

class UserDict(TypedDict, total=False):
    id: int
    username: str
    email: str
    created_at: str
    preferences: Dict[str, Any]

class ChatMessageDict(TypedDict, total=False):
    id: int
    user_id: int
    message: str
    response: str
    detected_mood: str
    detected_intensity: str
    timestamp: str

# ================== DATA CLASSES ==================
@dataclass
class MoodVector:
    """Represents a mood as a vector of scores"""
    energetic: float = 0.0
    happy: float = 0.0
    sad: float = 0.0
    stress: float = 0.0
    angry: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "energetic": self.energetic,
            "happy": self.happy,
            "sad": self.sad,
            "stress": self.stress,
            "angry": self.angry
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "MoodVector":
        return cls(
            energetic=data.get("energetic", 0.0),
            happy=data.get("happy", 0.0),
            sad=data.get("sad", 0.0),
            stress=data.get("stress", 0.0),
            angry=data.get("angry", 0.0)
        )
    
    def dominant_mood(self) -> str:
        """Returns the mood with highest score"""
        moods = self.to_dict()
        return max(moods, key=moods.get)

@dataclass
class AudioFeatures:
    """Represents audio features of a song"""
    energy: float = 50.0
    happiness: float = 50.0
    valence: float = 50.0
    danceability: float = 50.0
    acousticness: float = 50.0
    tempo: float = 120.0
    loudness: float = -10.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "energy": self.energy,
            "happiness": self.happiness,
            "valence": self.valence,
            "danceability": self.danceability,
            "acousticness": self.acousticness,
            "tempo": self.tempo,
            "loudness": self.loudness
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "AudioFeatures":
        return cls(
            energy=data.get("energy", 50.0),
            happiness=data.get("happiness", 50.0),
            valence=data.get("valence", 50.0),
            danceability=data.get("danceability", 50.0),
            acousticness=data.get("acousticness", 50.0),
            tempo=data.get("tempo", 120.0),
            loudness=data.get("loudness", -10.0)
        )

# Type alias for backward compatibility
Song = Dict[str, object]
