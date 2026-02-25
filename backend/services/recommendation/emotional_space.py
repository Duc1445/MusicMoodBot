"""
=============================================================================
EMOTIONAL VECTOR SPACE
=============================================================================

Represents moods in a 2D Valence-Arousal (VA) space for precise matching.

Mathematical Foundation:
========================

The Russell Circumplex Model places emotions on two axes:
- Valence (V): Pleasantness, ranging from -1 (negative) to +1 (positive)
- Arousal (A): Activation level, ranging from 0 (low) to 1 (high)

Any mood can be represented as a point (V, A) in this space.

Distance Metric:
---------------
For user emotional state U = (Vu, Au) and song S = (Vs, As):

    distance = √[(Vs - Vu)² + (As - Au)²]

The maximum possible distance in our space is:
    d_max = √[(1-(-1))² + (1-0)²] = √[4 + 1] = √5 ≈ 2.236

Similarity Conversion:
---------------------
We convert distance to similarity using:

    similarity = 1 - (distance / d_max)

This ensures similarity ∈ [0, 1].

Why VA Space is Superior to Categorical Matching:
-------------------------------------------------
1. **Granularity**: Captures nuances (e.g., "slightly sad" vs "very sad")
2. **Continuity**: Smooth transitions between emotional states
3. **Interpolation**: Can handle mixed emotions (e.g., "bittersweet")
4. **Measurability**: Objective comparison using Euclidean distance
5. **Flexibility**: Mood intensity is naturally represented by arousal

Author: MusicMoodBot Team
Version: 3.1.0
=============================================================================
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Maximum distance in VA space: sqrt((1-(-1))^2 + (1-0)^2) = sqrt(5)
VA_MAX_DISTANCE = math.sqrt(5)

# Valence range: [-1, 1]
VALENCE_MIN = -1.0
VALENCE_MAX = 1.0

# Arousal range: [0, 1]
AROUSAL_MIN = 0.0
AROUSAL_MAX = 1.0


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class EmotionalCoordinate:
    """
    A point in the Valence-Arousal emotional space.
    
    Attributes:
        valence: Pleasantness (-1 to +1)
        arousal: Activation level (0 to 1)
        confidence: How certain we are about this coordinate (0 to 1)
    """
    valence: float = 0.0
    arousal: float = 0.5
    confidence: float = 1.0
    
    def __post_init__(self):
        """Clamp values to valid ranges."""
        self.valence = max(VALENCE_MIN, min(VALENCE_MAX, self.valence))
        self.arousal = max(AROUSAL_MIN, min(AROUSAL_MAX, self.arousal))
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'valence': round(self.valence, 4),
            'arousal': round(self.arousal, 4),
            'confidence': round(self.confidence, 4),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmotionalCoordinate':
        return cls(
            valence=data.get('valence', 0.0),
            arousal=data.get('arousal', 0.5),
            confidence=data.get('confidence', 1.0),
        )
    
    def distance_to(self, other: 'EmotionalCoordinate') -> float:
        """Compute Euclidean distance to another coordinate."""
        return math.sqrt(
            (self.valence - other.valence) ** 2 +
            (self.arousal - other.arousal) ** 2
        )
    
    def similarity_to(self, other: 'EmotionalCoordinate') -> float:
        """Compute similarity score (0 to 1) to another coordinate."""
        distance = self.distance_to(other)
        return 1.0 - (distance / VA_MAX_DISTANCE)
    
    def weighted_average(self, other: 'EmotionalCoordinate', weight_self: float = 0.5) -> 'EmotionalCoordinate':
        """Compute weighted average with another coordinate."""
        weight_other = 1.0 - weight_self
        return EmotionalCoordinate(
            valence=weight_self * self.valence + weight_other * other.valence,
            arousal=weight_self * self.arousal + weight_other * other.arousal,
            confidence=min(self.confidence, other.confidence),
        )
    
    def __repr__(self) -> str:
        return f"EmotionalCoordinate(V={self.valence:.2f}, A={self.arousal:.2f})"


@dataclass
class MoodVector:
    """
    Named mood with its VA coordinates and metadata.
    """
    name: str
    name_vi: str
    coordinate: EmotionalCoordinate
    keywords: List[str] = field(default_factory=list)
    related_moods: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'name_vi': self.name_vi,
            'coordinate': self.coordinate.to_dict(),
            'keywords': self.keywords,
            'related_moods': self.related_moods,
        }


# =============================================================================
# MOOD DATABASE
# =============================================================================

# Predefined mood vectors in VA space
# Based on psychological research on emotion mapping
MOOD_VECTORS: Dict[str, MoodVector] = {
    'happy': MoodVector(
        name='happy',
        name_vi='Vui',
        coordinate=EmotionalCoordinate(valence=0.8, arousal=0.7),
        keywords=['vui', 'hạnh phúc', 'tươi', 'happy', 'joyful'],
        related_moods=['excited', 'energetic'],
    ),
    'sad': MoodVector(
        name='sad',
        name_vi='Buồn',
        coordinate=EmotionalCoordinate(valence=-0.7, arousal=0.2),
        keywords=['buồn', 'đau', 'khóc', 'sad', 'depressed'],
        related_moods=['melancholic', 'nostalgic'],
    ),
    'energetic': MoodVector(
        name='energetic',
        name_vi='Năng lượng',
        coordinate=EmotionalCoordinate(valence=0.5, arousal=0.9),
        keywords=['năng lượng', 'hype', 'sôi động', 'energetic', 'pumped'],
        related_moods=['happy', 'excited'],
    ),
    'calm': MoodVector(
        name='calm',
        name_vi='Bình yên',
        coordinate=EmotionalCoordinate(valence=0.3, arousal=0.2),
        keywords=['bình yên', 'thư giãn', 'calm', 'peaceful', 'serene'],
        related_moods=['chill', 'nostalgic'],
    ),
    'angry': MoodVector(
        name='angry',
        name_vi='Tức giận',
        coordinate=EmotionalCoordinate(valence=-0.8, arousal=0.9),
        keywords=['tức', 'giận', 'bực', 'angry', 'furious'],
        related_moods=['anxious', 'stress'],
    ),
    'romantic': MoodVector(
        name='romantic',
        name_vi='Lãng mạn',
        coordinate=EmotionalCoordinate(valence=0.6, arousal=0.4),
        keywords=['lãng mạn', 'yêu', 'romantic', 'love', 'tender'],
        related_moods=['happy', 'calm'],
    ),
    'nostalgic': MoodVector(
        name='nostalgic',
        name_vi='Hoài niệm',
        coordinate=EmotionalCoordinate(valence=0.1, arousal=0.3),
        keywords=['hoài niệm', 'nhớ', 'nostalgic', 'memories', 'reminiscent'],
        related_moods=['sad', 'calm'],
    ),
    'anxious': MoodVector(
        name='anxious',
        name_vi='Lo lắng',
        coordinate=EmotionalCoordinate(valence=-0.5, arousal=0.7),
        keywords=['lo lắng', 'bất an', 'anxious', 'worried', 'nervous'],
        related_moods=['stress', 'angry'],
    ),
    'stress': MoodVector(
        name='stress',
        name_vi='Suy tư',
        coordinate=EmotionalCoordinate(valence=-0.4, arousal=0.6),
        keywords=['suy tư', 'stress', 'căng thẳng', 'stressed', 'tense'],
        related_moods=['anxious', 'sad'],
    ),
    'chill': MoodVector(
        name='chill',
        name_vi='Chill',
        coordinate=EmotionalCoordinate(valence=0.4, arousal=0.3),
        keywords=['chill', 'lười', 'thư giãn', 'relaxed', 'laid-back'],
        related_moods=['calm', 'nostalgic'],
    ),
    'excited': MoodVector(
        name='excited',
        name_vi='Phấn khích',
        coordinate=EmotionalCoordinate(valence=0.7, arousal=0.85),
        keywords=['phấn khích', 'hào hứng', 'excited', 'thrilled'],
        related_moods=['happy', 'energetic'],
    ),
    'melancholic': MoodVector(
        name='melancholic',
        name_vi='U sầu',
        coordinate=EmotionalCoordinate(valence=-0.3, arousal=0.25),
        keywords=['u sầu', 'melancholic', 'gloomy', 'wistful'],
        related_moods=['sad', 'nostalgic'],
    ),
}


# =============================================================================
# EMOTIONAL VECTOR SPACE
# =============================================================================

class EmotionalVectorSpace:
    """
    Manages emotions in a 2D Valence-Arousal space.
    
    Provides:
    - Mood to coordinate mapping
    - Similarity computation
    - Interpolation between moods
    - Song matching in VA space
    
    Usage:
        space = EmotionalVectorSpace()
        
        # Get coordinates for a mood
        coord = space.get_coordinates('sad')
        
        # Compute similarity
        sim = space.compute_similarity(user_coord, song_coord)
        
        # Find nearest moods
        nearest = space.find_nearest_moods(coord, k=3)
    """
    
    def __init__(self):
        """Initialize with predefined mood vectors."""
        self.mood_vectors = MOOD_VECTORS.copy()
    
    def get_coordinates(self, mood: str) -> EmotionalCoordinate:
        """
        Get VA coordinates for a mood.
        
        Args:
            mood: Mood name (English or Vietnamese)
            
        Returns:
            EmotionalCoordinate for the mood
        """
        # Normalize mood name
        mood_lower = mood.lower().strip()
        
        # Direct lookup
        if mood_lower in self.mood_vectors:
            return self.mood_vectors[mood_lower].coordinate
        
        # Vietnamese lookup
        for mv in self.mood_vectors.values():
            if mv.name_vi.lower() == mood_lower:
                return mv.coordinate
        
        # Keyword matching
        for mv in self.mood_vectors.values():
            if any(kw in mood_lower for kw in mv.keywords):
                return mv.coordinate
        
        # Default to neutral
        logger.warning(f"Unknown mood '{mood}', using neutral coordinates")
        return EmotionalCoordinate(valence=0.0, arousal=0.5)
    
    def compute_similarity(
        self,
        coord1: EmotionalCoordinate,
        coord2: EmotionalCoordinate,
        use_confidence: bool = True
    ) -> float:
        """
        Compute similarity between two emotional coordinates.
        
        Args:
            coord1: First coordinate
            coord2: Second coordinate
            use_confidence: Scale by confidence
            
        Returns:
            Similarity score in [0, 1]
        """
        base_similarity = coord1.similarity_to(coord2)
        
        if use_confidence:
            # Reduce similarity if confidence is low
            confidence_factor = min(coord1.confidence, coord2.confidence)
            # Use sqrt to soften the penalty
            base_similarity *= math.sqrt(confidence_factor)
        
        return base_similarity
    
    def compute_distance(
        self,
        coord1: EmotionalCoordinate,
        coord2: EmotionalCoordinate
    ) -> float:
        """Compute Euclidean distance between coordinates."""
        return coord1.distance_to(coord2)
    
    def find_nearest_moods(
        self,
        coord: EmotionalCoordinate,
        k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Find k nearest mood categories to a coordinate.
        
        Args:
            coord: Target coordinate
            k: Number of moods to return
            
        Returns:
            List of (mood_name, similarity) tuples
        """
        similarities = []
        
        for name, mv in self.mood_vectors.items():
            sim = coord.similarity_to(mv.coordinate)
            similarities.append((name, sim))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:k]
    
    def interpolate_moods(
        self,
        moods: List[Tuple[str, float]]
    ) -> EmotionalCoordinate:
        """
        Interpolate between multiple moods with weights.
        
        Args:
            moods: List of (mood_name, weight) tuples
            
        Returns:
            Interpolated coordinate
        """
        if not moods:
            return EmotionalCoordinate()
        
        total_weight = sum(w for _, w in moods)
        if total_weight == 0:
            return self.get_coordinates(moods[0][0])
        
        v_sum = 0.0
        a_sum = 0.0
        
        for mood_name, weight in moods:
            coord = self.get_coordinates(mood_name)
            v_sum += coord.valence * weight
            a_sum += coord.arousal * weight
        
        return EmotionalCoordinate(
            valence=v_sum / total_weight,
            arousal=a_sum / total_weight,
        )
    
    def song_to_coordinate(self, song: Dict[str, Any]) -> EmotionalCoordinate:
        """
        Convert song features to emotional coordinate.
        
        Uses valence_score, arousal_score, energy, and mood.
        
        Args:
            song: Song dict with audio features
            
        Returns:
            Emotional coordinate for the song
        """
        # Try explicit VA scores first
        valence = song.get('valence_score')
        arousal = song.get('arousal_score')
        
        # Fallback to derived values
        if valence is None:
            valence = song.get('valence', 50)
            if isinstance(valence, (int, float)) and valence > 1:
                valence = (valence - 50) / 50  # 0-100 → -1 to 1
        
        if arousal is None:
            energy = song.get('energy', 50)
            if isinstance(energy, (int, float)) and energy > 1:
                arousal = energy / 100  # 0-100 → 0 to 1
            else:
                arousal = energy if isinstance(energy, float) else 0.5
        
        # If still no values, try mood-based coordinates
        song_mood = song.get('mood', '')
        if song_mood and (valence is None or arousal is None):
            mood_coord = self.get_coordinates(song_mood)
            if valence is None:
                valence = mood_coord.valence
            if arousal is None:
                arousal = mood_coord.arousal
        
        return EmotionalCoordinate(
            valence=float(valence) if valence is not None else 0.0,
            arousal=float(arousal) if arousal is not None else 0.5,
        )
    
    def rank_songs_by_emotional_distance(
        self,
        target: EmotionalCoordinate,
        songs: List[Dict[str, Any]],
        limit: int = None
    ) -> List[Tuple[Dict, float]]:
        """
        Rank songs by emotional similarity to target.
        
        Args:
            target: Target emotional coordinate
            songs: List of song dicts
            limit: Max results (None for all)
            
        Returns:
            List of (song, similarity) tuples sorted by similarity
        """
        scored = []
        
        for song in songs:
            song_coord = self.song_to_coordinate(song)
            similarity = self.compute_similarity(target, song_coord)
            scored.append((song, similarity))
        
        # Sort by similarity descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        if limit:
            return scored[:limit]
        return scored
    
    def get_quadrant(self, coord: EmotionalCoordinate) -> str:
        """
        Get the emotional quadrant for a coordinate.
        
        Quadrants:
        - Q1 (++): Happy/Excited (positive valence, high arousal)
        - Q2 (-+): Angry/Anxious (negative valence, high arousal)
        - Q3 (--): Sad/Depressed (negative valence, low arousal)
        - Q4 (+-): Calm/Relaxed (positive valence, low arousal)
        """
        if coord.valence >= 0 and coord.arousal >= 0.5:
            return 'Q1_HAPPY_EXCITED'
        elif coord.valence < 0 and coord.arousal >= 0.5:
            return 'Q2_ANGRY_ANXIOUS'
        elif coord.valence < 0 and coord.arousal < 0.5:
            return 'Q3_SAD_DEPRESSED'
        else:
            return 'Q4_CALM_RELAXED'
    
    def visualize(self, coordinates: List[Tuple[str, EmotionalCoordinate]]) -> str:
        """
        Generate ASCII visualization of coordinates in VA space.
        
        Args:
            coordinates: List of (label, coordinate) tuples
            
        Returns:
            ASCII art representation
        """
        # 21x11 grid
        width, height = 21, 11
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Draw axes
        for i in range(width):
            grid[height // 2][i] = '-'
        for j in range(height):
            grid[j][width // 2] = '|'
        grid[height // 2][width // 2] = '+'
        
        # Plot points
        for label, coord in coordinates:
            # Map valence [-1, 1] to x [0, width-1]
            x = int((coord.valence + 1) / 2 * (width - 1))
            # Map arousal [0, 1] to y [height-1, 0] (inverted)
            y = int((1 - coord.arousal) * (height - 1))
            
            x = max(0, min(width - 1, x))
            y = max(0, min(height - 1, y))
            
            grid[y][x] = label[0].upper()
        
        # Build output
        lines = ['Arousal (high)']
        lines.append('    ' + ''.join(grid[0]))
        for row in grid[1:-1]:
            lines.append('    ' + ''.join(row))
        lines.append('    ' + ''.join(grid[-1]))
        lines.append('Arousal (low)')
        lines.append('  Valence (-)           Valence (+)')
        
        return '\n'.join(lines)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def mood_to_va_coordinates(mood: str) -> Tuple[float, float]:
    """
    Convert mood category to VA coordinates.
    
    Args:
        mood: Mood name (English or Vietnamese)
        
    Returns:
        Tuple of (valence, arousal)
    """
    space = EmotionalVectorSpace()
    coord = space.get_coordinates(mood)
    return coord.valence, coord.arousal


def compute_va_similarity(
    v1: float, a1: float,
    v2: float, a2: float
) -> float:
    """
    Compute similarity between two VA coordinates.
    
    Args:
        v1, a1: First coordinate (valence, arousal)
        v2, a2: Second coordinate (valence, arousal)
        
    Returns:
        Similarity score in [0, 1]
    """
    coord1 = EmotionalCoordinate(valence=v1, arousal=a1)
    coord2 = EmotionalCoordinate(valence=v2, arousal=a2)
    return coord1.similarity_to(coord2)


def compute_va_distance(
    v1: float, a1: float,
    v2: float, a2: float
) -> float:
    """
    Compute Euclidean distance between two VA coordinates.
    
    Formula:
        distance = sqrt((v2 - v1)² + (a2 - a1)²)
    
    Args:
        v1, a1: First coordinate (valence, arousal)
        v2, a2: Second coordinate (valence, arousal)
        
    Returns:
        Distance value in [0, sqrt(5)]
    """
    return math.sqrt((v2 - v1) ** 2 + (a2 - a1) ** 2)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_emotional_space() -> EmotionalVectorSpace:
    """Create an EmotionalVectorSpace instance."""
    return EmotionalVectorSpace()
