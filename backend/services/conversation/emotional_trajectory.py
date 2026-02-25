"""
=============================================================================
EMOTIONAL TRAJECTORY TRACKER - v5.0
=============================================================================

Tracks emotional state changes across conversation turns using VA-space.

Features:
- Linear regression for trend detection
- DECLINING/STABLE/IMPROVING trajectory classification
- Comfort music triggering based on trajectory
- VA-space visualization support

Author: MusicMoodBot Team
Version: 5.0.0
=============================================================================
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import math


class EmotionalTrend(str, Enum):
    """Emotional trajectory trend classification."""
    DECLINING = "declining"      # User becoming more negative
    STABLE = "stable"            # No significant change
    IMPROVING = "improving"      # User becoming more positive
    VOLATILE = "volatile"        # High variance, unpredictable
    UNKNOWN = "unknown"          # Insufficient data


@dataclass
class VAPoint:
    """Point in Valence-Arousal space."""
    valence: float      # -1 (negative) to 1 (positive)
    arousal: float      # -1 (calm) to 1 (excited)
    turn: int
    mood: Optional[str] = None
    
    def distance_to(self, other: "VAPoint") -> float:
        """Calculate Euclidean distance to another VA point."""
        return math.sqrt(
            (self.valence - other.valence) ** 2 +
            (self.arousal - other.arousal) ** 2
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "valence": round(self.valence, 4),
            "arousal": round(self.arousal, 4),
            "turn": self.turn,
            "mood": self.mood
        }


class EmotionalTrajectoryTracker:
    """
    Tracks user's emotional trajectory across conversation turns.
    
    Uses linear regression on VA-space coordinates to detect trends.
    Triggers comfort music recommendations when trajectory is declining.
    """
    
    # Trend detection thresholds
    SLOPE_THRESHOLD_POSITIVE = 0.05   # Slope > 0.05 = improving
    SLOPE_THRESHOLD_NEGATIVE = -0.05  # Slope < -0.05 = declining
    VARIANCE_THRESHOLD = 0.3          # High variance = volatile
    MIN_POINTS_FOR_TREND = 3          # Minimum turns for trend detection
    
    # Mood centroids for reference (VA coordinates)
    MOOD_CENTROIDS: Dict[str, Tuple[float, float]] = {
        "happy": (0.8, 0.6),
        "sad": (-0.7, -0.3),
        "angry": (-0.6, 0.8),
        "calm": (0.5, -0.5),
        "excited": (0.7, 0.9),
        "romantic": (0.6, 0.2),
        "nostalgic": (0.1, -0.2),
        "energetic": (0.5, 0.9),
        "anxious": (-0.4, 0.7),
        "peaceful": (0.6, -0.6),
        "melancholic": (-0.5, -0.4),
        "neutral": (0.0, 0.0),
    }
    
    def __init__(self):
        self._points: List[VAPoint] = []
        self._valence_slope: float = 0.0
        self._arousal_slope: float = 0.0
        self._valence_variance: float = 0.0
        self._arousal_variance: float = 0.0
        self._current_trend: EmotionalTrend = EmotionalTrend.UNKNOWN
    
    @property
    def trajectory(self) -> List[VAPoint]:
        """Get all tracked VA points."""
        return self._points.copy()
    
    @property
    def current_trend(self) -> EmotionalTrend:
        """Get current emotional trend."""
        return self._current_trend
    
    @property
    def valence_slope(self) -> float:
        """Get valence slope (positive = improving)."""
        return self._valence_slope
    
    @property
    def arousal_slope(self) -> float:
        """Get arousal slope."""
        return self._arousal_slope
    
    def add_point(
        self,
        valence: float,
        arousal: float,
        turn: int,
        mood: Optional[str] = None
    ) -> VAPoint:
        """
        Add a new VA point to the trajectory.
        
        Args:
            valence: Valence score (-1 to 1)
            arousal: Arousal score (-1 to 1)
            turn: Conversation turn number
            mood: Optional detected mood label
            
        Returns:
            The created VAPoint
        """
        # Clamp values to valid range
        valence = max(-1.0, min(1.0, valence))
        arousal = max(-1.0, min(1.0, arousal))
        
        point = VAPoint(
            valence=valence,
            arousal=arousal,
            turn=turn,
            mood=mood
        )
        self._points.append(point)
        
        # Recalculate trend if we have enough points
        if len(self._points) >= self.MIN_POINTS_FOR_TREND:
            self._calculate_trend()
        
        return point
    
    def _calculate_trend(self):
        """Calculate trend using linear regression on VA coordinates."""
        n = len(self._points)
        if n < self.MIN_POINTS_FOR_TREND:
            self._current_trend = EmotionalTrend.UNKNOWN
            return
        
        # Extract coordinates
        turns = [p.turn for p in self._points]
        valences = [p.valence for p in self._points]
        arousals = [p.arousal for p in self._points]
        
        # Calculate means
        mean_turn = sum(turns) / n
        mean_valence = sum(valences) / n
        mean_arousal = sum(arousals) / n
        
        # Calculate slopes using least squares
        numerator_v = sum((t - mean_turn) * (v - mean_valence) for t, v in zip(turns, valences))
        numerator_a = sum((t - mean_turn) * (a - mean_arousal) for t, a in zip(turns, arousals))
        denominator = sum((t - mean_turn) ** 2 for t in turns)
        
        if denominator > 0:
            self._valence_slope = numerator_v / denominator
            self._arousal_slope = numerator_a / denominator
        else:
            self._valence_slope = 0.0
            self._arousal_slope = 0.0
        
        # Calculate variance
        self._valence_variance = sum((v - mean_valence) ** 2 for v in valences) / n
        self._arousal_variance = sum((a - mean_arousal) ** 2 for a in arousals) / n
        
        # Classify trend based on valence slope (primary indicator)
        if self._valence_variance > self.VARIANCE_THRESHOLD:
            self._current_trend = EmotionalTrend.VOLATILE
        elif self._valence_slope > self.SLOPE_THRESHOLD_POSITIVE:
            self._current_trend = EmotionalTrend.IMPROVING
        elif self._valence_slope < self.SLOPE_THRESHOLD_NEGATIVE:
            self._current_trend = EmotionalTrend.DECLINING
        else:
            self._current_trend = EmotionalTrend.STABLE
    
    def get_comfort_music_boost(self) -> float:
        """
        Calculate comfort music boost based on trajectory.
        
        Returns:
            Boost value (0.0 to 0.3) for comfort music scoring
        """
        if self._current_trend == EmotionalTrend.DECLINING:
            # Stronger boost for steeper decline
            decline_magnitude = abs(self._valence_slope)
            return min(0.3, decline_magnitude * 2.0)
        
        return 0.0
    
    def get_energy_adjustment(self) -> float:
        """
        Calculate energy level adjustment based on trajectory.
        
        For declining moods, suggest lower energy music.
        For improving moods, can increase energy gradually.
        
        Returns:
            Energy adjustment (-0.3 to 0.3)
        """
        if self._current_trend == EmotionalTrend.DECLINING:
            # Lower energy for sad trajectory
            return -0.2
        elif self._current_trend == EmotionalTrend.IMPROVING:
            # Slightly higher energy for positive trajectory
            return 0.1
        
        return 0.0
    
    def get_current_position(self) -> Optional[VAPoint]:
        """Get the most recent VA position."""
        return self._points[-1] if self._points else None
    
    def get_average_position(self, last_n: int = 3) -> Optional[Tuple[float, float]]:
        """
        Get average VA position over last n turns.
        
        Args:
            last_n: Number of recent turns to average
            
        Returns:
            Tuple of (avg_valence, avg_arousal) or None
        """
        if not self._points:
            return None
        
        recent = self._points[-last_n:]
        avg_valence = sum(p.valence for p in recent) / len(recent)
        avg_arousal = sum(p.arousal for p in recent) / len(recent)
        
        return (avg_valence, avg_arousal)
    
    def get_nearest_mood_to_current(self) -> Optional[str]:
        """
        Find the mood centroid nearest to current position.
        
        Returns:
            Mood name or None if no points
        """
        current = self.get_current_position()
        if current is None:
            return None
        
        min_distance = float('inf')
        nearest_mood = None
        
        for mood, (v, a) in self.MOOD_CENTROIDS.items():
            distance = math.sqrt(
                (current.valence - v) ** 2 +
                (current.arousal - a) ** 2
            )
            if distance < min_distance:
                min_distance = distance
                nearest_mood = mood
        
        return nearest_mood
    
    def predict_next_position(self) -> Optional[Tuple[float, float]]:
        """
        Predict next VA position based on current trend.
        
        Returns:
            Tuple of (predicted_valence, predicted_arousal)
        """
        if len(self._points) < self.MIN_POINTS_FOR_TREND:
            return None
        
        current = self._points[-1]
        next_turn = current.turn + 1
        
        # Linear extrapolation
        mean_turn = sum(p.turn for p in self._points) / len(self._points)
        mean_valence = sum(p.valence for p in self._points) / len(self._points)
        mean_arousal = sum(p.arousal for p in self._points) / len(self._points)
        
        predicted_valence = mean_valence + self._valence_slope * (next_turn - mean_turn)
        predicted_arousal = mean_arousal + self._arousal_slope * (next_turn - mean_turn)
        
        # Clamp to valid range
        predicted_valence = max(-1.0, min(1.0, predicted_valence))
        predicted_arousal = max(-1.0, min(1.0, predicted_arousal))
        
        return (predicted_valence, predicted_arousal)
    
    def get_analysis(self) -> Dict:
        """
        Get complete trajectory analysis.
        
        Returns:
            Dictionary with all trajectory metrics
        """
        avg_pos = self.get_average_position()
        predicted = self.predict_next_position()
        
        return {
            "point_count": len(self._points),
            "current_trend": self._current_trend.value,
            "valence_slope": round(self._valence_slope, 4),
            "arousal_slope": round(self._arousal_slope, 4),
            "valence_variance": round(self._valence_variance, 4),
            "arousal_variance": round(self._arousal_variance, 4),
            "comfort_music_boost": round(self.get_comfort_music_boost(), 4),
            "energy_adjustment": round(self.get_energy_adjustment(), 4),
            "current_position": self.get_current_position().to_dict() if self.get_current_position() else None,
            "average_position": {
                "valence": round(avg_pos[0], 4),
                "arousal": round(avg_pos[1], 4)
            } if avg_pos else None,
            "predicted_next": {
                "valence": round(predicted[0], 4),
                "arousal": round(predicted[1], 4)
            } if predicted else None,
            "nearest_mood": self.get_nearest_mood_to_current(),
            "trajectory": [p.to_dict() for p in self._points],
        }
    
    def to_dict(self) -> Dict:
        """Serialize tracker state."""
        return {
            "points": [p.to_dict() for p in self._points],
            "valence_slope": self._valence_slope,
            "arousal_slope": self._arousal_slope,
            "valence_variance": self._valence_variance,
            "arousal_variance": self._arousal_variance,
            "current_trend": self._current_trend.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionalTrajectoryTracker":
        """Deserialize from dictionary."""
        tracker = cls()
        
        for point_data in data.get("points", []):
            tracker._points.append(VAPoint(
                valence=point_data["valence"],
                arousal=point_data["arousal"],
                turn=point_data["turn"],
                mood=point_data.get("mood")
            ))
        
        tracker._valence_slope = data.get("valence_slope", 0.0)
        tracker._arousal_slope = data.get("arousal_slope", 0.0)
        tracker._valence_variance = data.get("valence_variance", 0.0)
        tracker._arousal_variance = data.get("arousal_variance", 0.0)
        tracker._current_trend = EmotionalTrend(data.get("current_trend", "unknown"))
        
        return tracker
    
    def reset(self):
        """Clear all tracked points."""
        self._points.clear()
        self._valence_slope = 0.0
        self._arousal_slope = 0.0
        self._valence_variance = 0.0
        self._arousal_variance = 0.0
        self._current_trend = EmotionalTrend.UNKNOWN


class EmotionalTrajectoryStore:
    """
    Store for managing per-user emotional trajectory trackers.
    
    For production, replace with Redis or database-backed store.
    """
    
    def __init__(self):
        self._trackers: Dict[int, EmotionalTrajectoryTracker] = {}
    
    def get(self, user_id: int) -> Optional[EmotionalTrajectoryTracker]:
        """Get tracker for user."""
        return self._trackers.get(user_id)
    
    def get_or_create(self, user_id: int) -> EmotionalTrajectoryTracker:
        """Get existing or create new tracker for user."""
        if user_id not in self._trackers:
            self._trackers[user_id] = EmotionalTrajectoryTracker()
        return self._trackers[user_id]
    
    def add_mood(self, user_id: int, mood: str) -> None:
        """Add mood point for user."""
        tracker = self.get_or_create(user_id)
        va = mood_to_va(mood)
        turn = len(tracker.trajectory) + 1
        tracker.add_point(va[0], va[1], turn, mood)
    
    def get_trend(self, user_id: int) -> Optional[EmotionalTrend]:
        """Get trend for user."""
        tracker = self._trackers.get(user_id)
        if tracker:
            return tracker.current_trend
        return None
    
    def get_comfort_boost(self, user_id: int) -> float:
        """Get comfort boost for user."""
        tracker = self._trackers.get(user_id)
        if tracker:
            return tracker.get_comfort_music_boost()
        return 0.0
    
    def get_history_count(self, user_id: int) -> int:
        """Get number of data points for user."""
        tracker = self._trackers.get(user_id)
        if tracker:
            return len(tracker.trajectory)
        return 0
    
    def delete(self, user_id: int) -> bool:
        """Delete tracker for user."""
        if user_id in self._trackers:
            del self._trackers[user_id]
            return True
        return False


# Global store instance
_trajectory_store: Optional[EmotionalTrajectoryStore] = None


def get_trajectory_tracker() -> EmotionalTrajectoryStore:
    """Get or create the global trajectory store."""
    global _trajectory_store
    if _trajectory_store is None:
        _trajectory_store = EmotionalTrajectoryStore()
    return _trajectory_store


def mood_to_va(mood: str) -> Tuple[float, float]:
    """
    Convert mood label to VA coordinates.
    
    Args:
        mood: Mood label (e.g., "happy", "sad")
        
    Returns:
        Tuple of (valence, arousal)
    """
    return EmotionalTrajectoryTracker.MOOD_CENTROIDS.get(
        mood.lower(),
        (0.0, 0.0)  # Default to neutral
    )


def va_to_mood(valence: float, arousal: float) -> str:
    """
    Convert VA coordinates to nearest mood label.
    
    Args:
        valence: Valence score (-1 to 1)
        arousal: Arousal score (-1 to 1)
        
    Returns:
        Mood label string
    """
    min_distance = float('inf')
    nearest_mood = "neutral"
    
    for mood, (v, a) in EmotionalTrajectoryTracker.MOOD_CENTROIDS.items():
        distance = math.sqrt((valence - v) ** 2 + (arousal - a) ** 2)
        if distance < min_distance:
            min_distance = distance
            nearest_mood = mood
    
    return nearest_mood
