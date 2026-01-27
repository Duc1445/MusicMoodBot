"""Ranking service for personalized song recommendations."""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple
from backend.src.ranking.preference_model import PreferenceModel, UserPreferenceTracker
from backend.src.services.constants import Song, MOODS


class RankingService:
    """
    Service for ranking songs based on user preferences and mood.
    
    Combines:
    - User preference learning (likes/dislikes)
    - Mood-based filtering
    - Personalized scoring
    """
    
    def __init__(self):
        """Initialize ranking service."""
        self.user_trackers: Dict[str, UserPreferenceTracker] = {}
        
    def get_tracker(self, user_id: str) -> UserPreferenceTracker:
        """Get or create user preference tracker."""
        if user_id not in self.user_trackers:
            self.user_trackers[user_id] = UserPreferenceTracker(user_id)
        return self.user_trackers[user_id]
    
    def record_feedback(
        self, 
        user_id: str, 
        song: Song, 
        liked: bool
    ) -> Dict[str, object]:
        """
        Record user feedback (like/dislike) for a song.
        
        Args:
            user_id: User identifier
            song: Song dictionary
            liked: True if user liked, False if disliked
            
        Returns:
            Feedback statistics
        """
        tracker = self.get_tracker(user_id)
        preference = 1 if liked else 0
        tracker.record_preference(song, preference)
        
        # Auto-retrain if enough data
        if len(tracker.feedback) >= 5 and len(tracker.feedback) % 5 == 0:
            tracker.retrain()
            
        return tracker.get_stats()
    
    def rank_songs(
        self,
        user_id: str,
        songs: List[Song],
        target_mood: Optional[str] = None,
        top_k: int = 10
    ) -> List[Tuple[Song, float]]:
        """
        Rank songs based on user preferences and optional mood filter.
        
        Args:
            user_id: User identifier
            songs: List of songs to rank
            target_mood: Optional mood filter (energetic, happy, sad, stress, angry)
            top_k: Number of top results
            
        Returns:
            List of (song, score) tuples sorted by relevance
        """
        tracker = self.get_tracker(user_id)
        
        # Filter by mood if specified
        if target_mood and target_mood in MOODS:
            songs = [s for s in songs if s.get('mood') == target_mood]
        
        # Score songs
        scored_songs: List[Tuple[Song, float]] = []
        for song in songs:
            score = self._calculate_song_score(tracker, song, target_mood)
            scored_songs.append((song, score))
        
        # Sort by score descending
        scored_songs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_songs[:top_k]
    
    def _calculate_song_score(
        self,
        tracker: UserPreferenceTracker,
        song: Song,
        target_mood: Optional[str] = None
    ) -> float:
        """
        Calculate personalized score for a song.
        
        Score combines:
        - User preference probability (from ML model)
        - Mood confidence (how well song matches predicted mood)
        - Intensity preference (optional)
        """
        # Base score from user preference model
        base_score = tracker.predict_preference(song)
        
        # Boost for mood match
        mood_boost = 0.0
        if target_mood:
            song_mood = song.get('mood', '')
            if song_mood == target_mood:
                mood_boost = 0.2
            elif self._is_similar_mood(song_mood, target_mood):
                mood_boost = 0.1
        
        # Mood confidence boost
        confidence = float(song.get('mood_confidence', 0.5))
        confidence_boost = confidence * 0.1
        
        # Calculate final score
        final_score = base_score + mood_boost + confidence_boost
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, final_score))
    
    def _is_similar_mood(self, mood1: str, mood2: str) -> bool:
        """Check if two moods are similar."""
        similar_groups = [
            {'energetic', 'happy'},
            {'sad', 'stress'},
            {'stress', 'angry'},
        ]
        for group in similar_groups:
            if mood1 in group and mood2 in group:
                return True
        return False
    
    def get_recommendations(
        self,
        user_id: str,
        songs: List[Song],
        mood: Optional[str] = None,
        diversity: float = 0.3,
        top_k: int = 10
    ) -> List[Song]:
        """
        Get personalized recommendations with diversity.
        
        Args:
            user_id: User identifier
            songs: Pool of songs to recommend from
            mood: Optional mood filter
            diversity: How much variety to include (0-1)
            top_k: Number of recommendations
            
        Returns:
            List of recommended songs
        """
        # Get ranked songs
        ranked = self.rank_songs(user_id, songs, mood, top_k=top_k * 3)
        
        if not ranked:
            return []
        
        # Add diversity by sampling
        if diversity > 0 and len(ranked) > top_k:
            import random
            
            # Take top half strictly by score
            strict_count = int(top_k * (1 - diversity))
            diverse_count = top_k - strict_count
            
            recommendations = [s for s, _ in ranked[:strict_count]]
            
            # Sample remaining with probability proportional to score
            remaining = ranked[strict_count:]
            if remaining and diverse_count > 0:
                weights = [score for _, score in remaining]
                total_weight = sum(weights) or 1.0
                probs = [w / total_weight for w in weights]
                
                # Sample without replacement
                sample_size = min(diverse_count, len(remaining))
                sampled_indices = []
                for _ in range(sample_size):
                    if not probs:
                        break
                    # Weighted random choice
                    r = random.random()
                    cumsum = 0
                    for i, p in enumerate(probs):
                        cumsum += p
                        if r <= cumsum:
                            sampled_indices.append(i)
                            probs.pop(i)
                            remaining.pop(i)
                            break
                
                for idx in sampled_indices:
                    if idx < len(ranked[strict_count:]):
                        recommendations.append(ranked[strict_count + idx][0])
            
            return recommendations[:top_k]
        else:
            return [s for s, _ in ranked[:top_k]]
    
    def get_user_stats(self, user_id: str) -> Dict[str, object]:
        """Get user preference statistics."""
        tracker = self.get_tracker(user_id)
        stats = tracker.get_stats()
        
        # Add model status
        stats['model_trained'] = tracker.model.is_fitted
        stats['user_id'] = user_id
        
        return stats


# Singleton instance
_ranking_service: Optional[RankingService] = None


def get_ranking_service() -> RankingService:
    """Get or create ranking service singleton."""
    global _ranking_service
    if _ranking_service is None:
        _ranking_service = RankingService()
    return _ranking_service
