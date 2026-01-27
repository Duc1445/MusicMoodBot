"""
Mood transition suggestion engine.
Provides smooth mood transitions and journey recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging

from backend.src.services.constants import MOODS, MOOD_EN_TO_VI, MOOD_EMOJI

logger = logging.getLogger(__name__)


class TransitionSpeed(Enum):
    """Speed of mood transition."""
    GRADUAL = "gradual"   # 5-7 songs
    MODERATE = "moderate"  # 3-4 songs
    QUICK = "quick"       # 1-2 songs


@dataclass
class MoodTransition:
    """A single step in mood transition."""
    mood: str
    intensity_target: int  # 1-3
    feature_targets: Dict[str, float]
    description: str


@dataclass
class TransitionPath:
    """Complete path from source to target mood."""
    source_mood: str
    target_mood: str
    steps: List[MoodTransition]
    estimated_songs: int
    transition_speed: TransitionSpeed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_mood": self.source_mood,
            "target_mood": self.target_mood,
            "steps": [
                {
                    "mood": s.mood,
                    "intensity": s.intensity_target,
                    "targets": s.feature_targets,
                    "description": s.description
                }
                for s in self.steps
            ],
            "estimated_songs": self.estimated_songs,
            "speed": self.transition_speed.value
        }


class MoodTransitionEngine:
    """
    Engine for suggesting smooth mood transitions.
    
    Features:
    - Calculate optimal transition paths
    - Generate transition playlists
    - Respect psychological mood flow
    """
    
    # Mood positions in 2D VA space (Valence, Arousal)
    MOOD_POSITIONS = {
        "energetic": (75, 80),  # High V, High A
        "happy": (80, 35),      # High V, Low A
        "sad": (25, 25),        # Low V, Low A
        "stress": (30, 75),     # Low V, High A
        "angry": (20, 85),      # Low V, Very High A
    }
    
    # Natural mood transitions (psychologically comfortable)
    NATURAL_TRANSITIONS = {
        "energetic": ["happy", "stress"],
        "happy": ["energetic", "sad"],  # through chill
        "sad": ["happy", "stress"],
        "stress": ["energetic", "sad", "angry"],
        "angry": ["stress", "energetic"],
    }
    
    # Intensity features
    INTENSITY_FEATURES = {
        1: {"energy": 35, "tempo": 90, "loudness": -12},   # Low
        2: {"energy": 55, "tempo": 110, "loudness": -8},   # Medium
        3: {"energy": 80, "tempo": 130, "loudness": -4},   # High
    }
    
    def __init__(self):
        self._path_cache: Dict[Tuple[str, str], List[str]] = {}
    
    def _mood_distance(self, mood1: str, mood2: str) -> float:
        """Calculate distance between two moods in VA space."""
        pos1 = self.MOOD_POSITIONS.get(mood1, (50, 50))
        pos2 = self.MOOD_POSITIONS.get(mood2, (50, 50))
        
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
    
    def _find_shortest_path(
        self,
        source: str,
        target: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find shortest natural transition path using BFS."""
        if source == target:
            return [source]
        
        cache_key = (source, target)
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]
        
        visited = {source}
        queue = [(source, [source])]
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            for neighbor in self.NATURAL_TRANSITIONS.get(current, []):
                if neighbor == target:
                    result = path + [target]
                    self._path_cache[cache_key] = result
                    return result
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        # No natural path found, use direct transition
        return [source, target]
    
    def _interpolate_features(
        self,
        start_mood: str,
        end_mood: str,
        progress: float  # 0.0 to 1.0
    ) -> Dict[str, float]:
        """Interpolate feature targets between moods."""
        start_pos = self.MOOD_POSITIONS.get(start_mood, (50, 50))
        end_pos = self.MOOD_POSITIONS.get(end_mood, (50, 50))
        
        # Interpolate VA
        valence = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
        arousal = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
        
        # Convert to features
        return {
            "energy": arousal,
            "happiness": valence,
            "danceability": (valence + arousal) / 2,
            "tempo": 70 + arousal * 1.2,  # 70-190 BPM based on arousal
        }
    
    def _generate_description(
        self,
        from_mood: str,
        to_mood: str,
        is_final: bool = False
    ) -> str:
        """Generate human-readable description for transition step."""
        from_vi = MOOD_EN_TO_VI.get(from_mood, from_mood)
        to_vi = MOOD_EN_TO_VI.get(to_mood, to_mood)
        emoji = MOOD_EMOJI.get(to_mood, "🎵")
        
        if is_final:
            return f"{emoji} Đích đến: {to_vi}"
        
        return f"Chuyển từ {from_vi} → {to_vi} {emoji}"
    
    def calculate_transition(
        self,
        source_mood: str,
        target_mood: str,
        speed: TransitionSpeed = TransitionSpeed.MODERATE
    ) -> TransitionPath:
        """
        Calculate optimal transition path between moods.
        
        Args:
            source_mood: Starting mood (English)
            target_mood: Target mood (English)
            speed: How quickly to transition
            
        Returns:
            TransitionPath with steps and song estimates
        """
        # Find path
        path = self._find_shortest_path(source_mood.lower(), target_mood.lower())
        
        if not path:
            path = [source_mood, target_mood]
        
        # Calculate steps based on speed
        songs_per_step = {
            TransitionSpeed.GRADUAL: 3,
            TransitionSpeed.MODERATE: 2,
            TransitionSpeed.QUICK: 1,
        }
        step_songs = songs_per_step[speed]
        
        steps: List[MoodTransition] = []
        
        for i in range(1, len(path)):
            prev_mood = path[i - 1]
            curr_mood = path[i]
            is_final = (i == len(path) - 1)
            
            # Determine intensity progression
            # Start with current intensity, gradually shift
            if i == 1:
                intensity = 2  # Start medium
            elif is_final:
                # Match target mood typical intensity
                intensity = {
                    "energetic": 3,
                    "angry": 3,
                    "happy": 2,
                    "stress": 2,
                    "sad": 1,
                }.get(curr_mood, 2)
            else:
                intensity = 2  # Medium for transitions
            
            # Interpolate features (end of this step)
            progress = i / (len(path) - 1) if len(path) > 1 else 1.0
            features = self._interpolate_features(source_mood, target_mood, progress)
            
            step = MoodTransition(
                mood=curr_mood,
                intensity_target=intensity,
                feature_targets=features,
                description=self._generate_description(prev_mood, curr_mood, is_final)
            )
            steps.append(step)
        
        estimated_total = len(steps) * step_songs
        
        return TransitionPath(
            source_mood=source_mood,
            target_mood=target_mood,
            steps=steps,
            estimated_songs=estimated_total,
            transition_speed=speed
        )
    
    def get_transition_playlist(
        self,
        source_mood: str,
        target_mood: str,
        all_songs: List[Dict],
        speed: TransitionSpeed = TransitionSpeed.MODERATE,
        songs_per_step: int = 2
    ) -> List[Dict]:
        """
        Generate actual playlist for mood transition.
        
        Args:
            source_mood: Starting mood
            target_mood: Target mood
            all_songs: Available songs
            speed: Transition speed
            songs_per_step: Songs per transition step
            
        Returns:
            Ordered list of songs for the transition
        """
        path = self.calculate_transition(source_mood, target_mood, speed)
        playlist = []
        
        for step in path.steps:
            target_features = step.feature_targets
            step_mood = step.mood
            
            # Find best matching songs
            candidates = []
            for song in all_songs:
                if song.get("song_id") in [s.get("song_id") for s in playlist]:
                    continue  # Skip already added
                
                # Calculate match score
                score = 0.0
                
                # Mood match bonus
                if song.get("mood") == step_mood:
                    score += 50
                
                # Feature matching
                for feature, target in target_features.items():
                    song_val = song.get(feature)
                    if song_val is not None:
                        diff = abs(float(song_val) - target)
                        score += max(0, 25 - diff * 0.3)
                
                candidates.append((song, score))
            
            # Sort by score and take best
            candidates.sort(key=lambda x: x[1], reverse=True)
            for song, _ in candidates[:songs_per_step]:
                song_with_step = {**song, "transition_step": step.description}
                playlist.append(song_with_step)
        
        return playlist
    
    def suggest_next_mood(
        self,
        current_mood: str,
        time_of_day: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest next moods based on current mood and context.
        
        Args:
            current_mood: Current mood (English)
            time_of_day: morning/afternoon/evening/night
            
        Returns:
            List of suggested moods with reasons
        """
        suggestions = []
        
        # Natural transitions
        natural = self.NATURAL_TRANSITIONS.get(current_mood.lower(), [])
        for mood in natural:
            mood_vi = MOOD_EN_TO_VI.get(mood, mood)
            emoji = MOOD_EMOJI.get(mood, "🎵")
            suggestions.append({
                "mood": mood,
                "mood_vi": mood_vi,
                "emoji": emoji,
                "reason": "Chuyển tự nhiên",
                "priority": 1
            })
        
        # Time-based suggestions
        time_moods = {
            "morning": ["energetic", "happy"],
            "afternoon": ["happy", "energetic"],
            "evening": ["happy", "sad"],
            "night": ["sad", "stress"],
        }
        
        if time_of_day and time_of_day in time_moods:
            for mood in time_moods[time_of_day]:
                if mood != current_mood and mood not in natural:
                    mood_vi = MOOD_EN_TO_VI.get(mood, mood)
                    emoji = MOOD_EMOJI.get(mood, "🎵")
                    suggestions.append({
                        "mood": mood,
                        "mood_vi": mood_vi,
                        "emoji": emoji,
                        "reason": f"Phù hợp với {time_of_day}",
                        "priority": 2
                    })
        
        # Add all moods as options (lower priority)
        for mood in MOODS:
            if mood != current_mood and mood not in [s["mood"] for s in suggestions]:
                mood_vi = MOOD_EN_TO_VI.get(mood, mood)
                emoji = MOOD_EMOJI.get(mood, "🎵")
                distance = self._mood_distance(current_mood, mood)
                suggestions.append({
                    "mood": mood,
                    "mood_vi": mood_vi,
                    "emoji": emoji,
                    "reason": "Khám phá mới",
                    "priority": 3,
                    "distance": round(distance, 1)
                })
        
        # Sort by priority
        suggestions.sort(key=lambda x: x["priority"])
        
        return suggestions
    
    def get_mood_journey(
        self,
        duration_minutes: int = 60,
        start_mood: Optional[str] = None,
        end_mood: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Plan a complete mood journey for a time duration.
        
        Args:
            duration_minutes: Total journey duration
            start_mood: Starting mood (or random)
            end_mood: Ending mood (or natural progression)
            
        Returns:
            Journey plan with phases
        """
        import random
        
        # Estimate songs (3.5 min average)
        total_songs = int(duration_minutes / 3.5)
        
        if start_mood is None:
            start_mood = random.choice(MOODS)
        
        # Plan phases
        if duration_minutes <= 20:
            # Short: 1-2 moods
            phases = [start_mood]
            if end_mood and end_mood != start_mood:
                phases.append(end_mood)
        elif duration_minutes <= 45:
            # Medium: 2-3 moods
            middle = random.choice(self.NATURAL_TRANSITIONS.get(start_mood, MOODS))
            phases = [start_mood, middle]
            if end_mood:
                phases.append(end_mood)
        else:
            # Long: 3-4 moods journey
            path = [start_mood]
            current = start_mood
            for _ in range(2):
                next_options = self.NATURAL_TRANSITIONS.get(current, MOODS)
                next_mood = random.choice([m for m in next_options if m not in path] or next_options)
                path.append(next_mood)
                current = next_mood
            if end_mood and end_mood not in path:
                path.append(end_mood)
            phases = path
        
        # Distribute songs
        songs_per_phase = total_songs // len(phases)
        
        journey_phases = []
        for i, mood in enumerate(phases):
            phase_start = i * (duration_minutes // len(phases))
            phase_songs = songs_per_phase + (1 if i < total_songs % len(phases) else 0)
            
            journey_phases.append({
                "phase": i + 1,
                "mood": mood,
                "mood_vi": MOOD_EN_TO_VI.get(mood, mood),
                "emoji": MOOD_EMOJI.get(mood, "🎵"),
                "start_minute": phase_start,
                "songs": phase_songs,
                "description": self._get_phase_description(i, len(phases), mood)
            })
        
        return {
            "total_duration_minutes": duration_minutes,
            "total_songs": total_songs,
            "phases": journey_phases,
            "start_mood": start_mood,
            "end_mood": phases[-1]
        }
    
    def _get_phase_description(self, phase_index: int, total_phases: int, mood: str) -> str:
        """Generate phase description."""
        mood_vi = MOOD_EN_TO_VI.get(mood, mood)
        
        if phase_index == 0:
            return f"Khởi đầu với {mood_vi}"
        elif phase_index == total_phases - 1:
            return f"Kết thúc với {mood_vi}"
        else:
            return f"Chuyển sang {mood_vi}"


# Global instance
_transition_engine: Optional[MoodTransitionEngine] = None


def get_transition_engine() -> MoodTransitionEngine:
    """Get or create transition engine instance."""
    global _transition_engine
    if _transition_engine is None:
        _transition_engine = MoodTransitionEngine()
    return _transition_engine


# Convenience functions
def suggest_transition(
    current_mood: str,
    target_mood: str,
    speed: str = "moderate"
) -> Dict[str, Any]:
    """Quick transition suggestion."""
    engine = get_transition_engine()
    speed_map = {
        "gradual": TransitionSpeed.GRADUAL,
        "moderate": TransitionSpeed.MODERATE,
        "quick": TransitionSpeed.QUICK,
    }
    transition = engine.calculate_transition(
        current_mood, target_mood, speed_map.get(speed, TransitionSpeed.MODERATE)
    )
    return transition.to_dict()
