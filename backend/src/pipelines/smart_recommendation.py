"""
Smart Recommendation Engine
Combines multiple algorithms for optimal song recommendations
"""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import random
import math


@dataclass
class RecommendationContext:
    """Context for generating recommendations"""
    user_id: Optional[str] = None
    mood: Optional[str] = None
    mood_vi: Optional[str] = None
    intensity: Optional[str] = None
    time_of_day: Optional[str] = None  # morning, afternoon, evening, night
    weather: Optional[str] = None  # sunny, rainy, cloudy
    activity: Optional[str] = None  # working, relaxing, exercising, commuting
    previous_songs: List[int] = None  # Recently played song IDs


class SmartRecommendationEngine:
    """
    Advanced recommendation engine that combines:
    - Content-based filtering (mood, genre, audio features)
    - Collaborative filtering (user preferences)
    - Context-aware recommendations
    - Diversity optimization
    """
    
    # Time-based mood mapping
    TIME_MOOD_BOOST = {
        "morning": {"energetic": 0.2, "happy": 0.1},
        "afternoon": {"happy": 0.1, "energetic": 0.1},
        "evening": {"sad": 0.1, "stress": 0.05},
        "night": {"sad": 0.15, "stress": 0.1, "happy": -0.1}
    }
    
    # Activity-based mood mapping
    ACTIVITY_MOOD_BOOST = {
        "working": {"stress": 0.1, "energetic": 0.05},
        "relaxing": {"happy": 0.15, "sad": 0.1},
        "exercising": {"energetic": 0.3, "happy": 0.1},
        "commuting": {"happy": 0.1, "energetic": 0.05}
    }
    
    # Weather-based mood mapping
    WEATHER_MOOD_BOOST = {
        "sunny": {"happy": 0.15, "energetic": 0.1},
        "rainy": {"sad": 0.2, "stress": 0.1},
        "cloudy": {"stress": 0.1, "sad": 0.05}
    }
    
    def __init__(self, preference_model=None):
        """
        Initialize with optional preference model.
        
        Args:
            preference_model: Trained PreferenceModel instance
        """
        self.preference_model = preference_model
        self.genre_similarity = self._build_genre_similarity()
    
    def _build_genre_similarity(self) -> Dict[str, List[str]]:
        """Build genre similarity mapping"""
        return {
            "pop": ["dance", "r&b", "electronic"],
            "rock": ["metal", "alternative", "indie"],
            "hip hop": ["rap", "r&b", "trap"],
            "electronic": ["edm", "dance", "house"],
            "r&b": ["soul", "pop", "hip hop"],
            "jazz": ["blues", "soul", "classical"],
            "classical": ["jazz", "instrumental"],
            "ballad": ["pop", "r&b", "soul"],
            "indie": ["alternative", "rock", "folk"],
            "v-pop": ["pop", "ballad", "r&b"]
        }
    
    def recommend(
        self,
        songs: List[Dict],
        context: RecommendationContext,
        top_k: int = 10,
        diversity: float = 0.3
    ) -> List[Dict]:
        """
        Generate recommendations based on context.
        
        Args:
            songs: Pool of songs to recommend from
            context: Recommendation context
            top_k: Number of recommendations
            diversity: Diversity factor (0-1)
            
        Returns:
            List of recommended songs with scores
        """
        if not songs:
            return []
        
        # Score all songs
        scored_songs = []
        for song in songs:
            score = self._calculate_score(song, context)
            scored_songs.append((song, score))
        
        # Sort by score
        scored_songs.sort(key=lambda x: x[1], reverse=True)
        
        # Apply diversity sampling
        if diversity > 0:
            recommendations = self._diverse_sample(scored_songs, top_k, diversity)
        else:
            recommendations = [s for s, _ in scored_songs[:top_k]]
        
        # Filter out recently played
        if context.previous_songs:
            recommendations = [
                s for s in recommendations 
                if s.get('song_id') not in context.previous_songs
            ]
        
        # Add recommendation metadata
        for song in recommendations:
            song['recommendation_score'] = next(
                (score for s, score in scored_songs if s.get('song_id') == song.get('song_id')),
                0.5
            )
        
        return recommendations[:top_k]
    
    def _calculate_score(self, song: Dict, context: RecommendationContext) -> float:
        """Calculate recommendation score for a song"""
        score = 0.5  # Base score
        
        # 1. Mood matching (primary factor)
        if context.mood:
            song_mood = song.get('mood', '')
            if song_mood == context.mood:
                score += 0.3
            elif self._is_similar_mood(song_mood, context.mood):
                score += 0.15
        
        # 2. Mood confidence
        confidence = float(song.get('mood_confidence', 0.5) or 0.5)
        score += confidence * 0.1
        
        # 3. Intensity matching
        if context.intensity:
            song_intensity = song.get('intensity', 2)
            intensity_map = {"Nhẹ": 1, "Vừa": 2, "Mạnh": 3, "low": 1, "medium": 2, "high": 3}
            target = intensity_map.get(context.intensity, 2)
            diff = abs(song_intensity - target)
            score += (1 - diff / 2) * 0.1
        
        # 4. Time-of-day boost
        if context.time_of_day and song.get('mood'):
            boosts = self.TIME_MOOD_BOOST.get(context.time_of_day, {})
            score += boosts.get(song.get('mood'), 0)
        
        # 5. Activity boost
        if context.activity and song.get('mood'):
            boosts = self.ACTIVITY_MOOD_BOOST.get(context.activity, {})
            score += boosts.get(song.get('mood'), 0)
        
        # 6. Weather boost
        if context.weather and song.get('mood'):
            boosts = self.WEATHER_MOOD_BOOST.get(context.weather, {})
            score += boosts.get(song.get('mood'), 0)
        
        # 7. User preference model (if available)
        if self.preference_model and hasattr(self.preference_model, 'predict_proba'):
            try:
                _, prob_like = self.preference_model.predict_proba(song)
                score += float(prob_like) * 0.2
            except:
                pass
        
        # Clamp score
        return max(0.0, min(1.0, score))
    
    def _is_similar_mood(self, mood1: str, mood2: str) -> bool:
        """Check if moods are similar"""
        similar_groups = [
            {'energetic', 'happy'},
            {'sad', 'stress'},
            {'stress', 'angry'}
        ]
        for group in similar_groups:
            if mood1 in group and mood2 in group:
                return True
        return False
    
    def _diverse_sample(
        self,
        scored_songs: List[Tuple[Dict, float]],
        top_k: int,
        diversity: float
    ) -> List[Dict]:
        """Sample songs with genre diversity"""
        if not scored_songs:
            return []
        
        # Take top portion strictly
        strict_count = max(1, int(top_k * (1 - diversity)))
        result = [s for s, _ in scored_songs[:strict_count]]
        
        # Get genres already selected
        selected_genres = set(s.get('genre', '').lower() for s in result)
        
        # Sample remaining with genre diversity
        remaining = scored_songs[strict_count:]
        while len(result) < top_k and remaining:
            # Prefer songs with different genres
            for i, (song, score) in enumerate(remaining):
                genre = song.get('genre', '').lower()
                if genre not in selected_genres:
                    result.append(song)
                    selected_genres.add(genre)
                    remaining.pop(i)
                    break
            else:
                # No different genre found, take highest score
                song, _ = remaining.pop(0)
                result.append(song)
        
        return result
    
    def explain_recommendation(self, song: Dict, context: RecommendationContext) -> str:
        """Generate explanation for why song was recommended"""
        reasons = []
        
        song_name = song.get('song_name', song.get('name', 'Bài hát'))
        artist = song.get('artist', 'Nghệ sĩ')
        
        # Mood match
        if context.mood and song.get('mood') == context.mood:
            reasons.append(f"phù hợp tâm trạng {context.mood_vi or context.mood}")
        
        # Intensity match
        if context.intensity:
            intensity_text = {"Nhẹ": "nhẹ nhàng", "Vừa": "vừa phải", "Mạnh": "sôi động"}
            reasons.append(f"nhịp điệu {intensity_text.get(context.intensity, context.intensity)}")
        
        # Time context
        if context.time_of_day:
            time_text = {
                "morning": "buổi sáng", 
                "afternoon": "buổi chiều",
                "evening": "buổi tối",
                "night": "đêm khuya"
            }
            reasons.append(f"thích hợp cho {time_text.get(context.time_of_day, '')}")
        
        # Activity context
        if context.activity:
            activity_text = {
                "working": "làm việc",
                "relaxing": "thư giãn",
                "exercising": "tập thể dục",
                "commuting": "di chuyển"
            }
            reasons.append(f"tốt khi {activity_text.get(context.activity, '')}")
        
        if reasons:
            reason_text = ", ".join(reasons)
            return f"'{song_name}' của {artist} được gợi ý vì {reason_text}."
        
        return f"'{song_name}' của {artist} là lựa chọn phù hợp cho bạn."


def create_smart_engine(preference_model=None) -> SmartRecommendationEngine:
    """Factory function to create smart recommendation engine"""
    return SmartRecommendationEngine(preference_model)
