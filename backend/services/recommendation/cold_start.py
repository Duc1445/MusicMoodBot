"""
=============================================================================
COLD START HANDLER - v5.0
=============================================================================

Handles cold start scenarios for new users and new songs.

Features:
- Popularity baseline strategy
- Mood cluster bootstrap
- Hybrid fallback with gradual transition

Author: MusicMoodBot Team
Version: 5.0.0
=============================================================================
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import sqlite3
import math
import os


@dataclass
class ColdStartSong:
    """Song recommended via cold start strategy."""
    song_id: int
    name: str
    artist: str
    genre: Optional[str]
    mood: Optional[str]
    score: float
    strategy: str
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "name": self.name,
            "artist": self.artist,
            "genre": self.genre,
            "mood": self.mood,
            "score": round(self.score, 4),
            "strategy": self.strategy,
            "explanation": self.explanation,
        }


class ColdStartHandler:
    """
    Handles recommendation for users with insufficient history.
    
    Strategies:
    1. Popularity Baseline: Recommend globally popular songs
    2. Mood Cluster Bootstrap: Recommend from mood cluster if mood is known
    3. Hybrid: Blend popularity with mood-based recommendations
    """
    
    # Cold start threshold (feedback count below this = cold start)
    COLD_START_THRESHOLD = 10
    
    # Transition range for gradual personalization
    TRANSITION_COMPLETE_AT = 30
    
    # VA-Space mood centroids
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
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__),
            "..", "..", "src", "database", "music.db"
        )
    
    def is_cold_start(self, user_id: int) -> bool:
        """
        Check if user is in cold start state.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user has insufficient feedback history
        """
        feedback_count = self._get_user_feedback_count(user_id)
        return feedback_count < self.COLD_START_THRESHOLD
    
    def get_personalization_weight(self, user_id: int) -> float:
        """
        Calculate personalization weight based on feedback history.
        
        Returns value from 0 (pure cold start) to 1 (full personalization).
        """
        feedback_count = self._get_user_feedback_count(user_id)
        
        if feedback_count >= self.TRANSITION_COMPLETE_AT:
            return 1.0
        elif feedback_count <= 0:
            return 0.0
        else:
            # Linear transition
            return feedback_count / self.TRANSITION_COMPLETE_AT
    
    def _get_user_feedback_count(self, user_id: int) -> int:
        """Get total feedback count for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try different possible feedback tables
            for table in ["feedback", "chat_history", "recommendations"]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = ?", (user_id,))
                    count = cursor.fetchone()[0]
                    conn.close()
                    return count
                except:
                    continue
            
            conn.close()
            return 0
        except Exception as e:
            print(f"Error getting feedback count: {e}")
            return 0
    
    def get_recommendations(
        self,
        user_id: int,
        mood: Optional[str] = None,
        limit: int = 10,
    ) -> Tuple[List[ColdStartSong], str, float]:
        """
        Get cold start recommendations.
        
        Args:
            user_id: User ID
            mood: Optional target mood
            limit: Number of recommendations
            
        Returns:
            Tuple of (songs, strategy_used, personalization_weight)
        """
        personalization_weight = self.get_personalization_weight(user_id)
        
        if personalization_weight >= 1.0:
            # Not cold start - should use normal recommendation
            return [], "none", personalization_weight
        
        if mood:
            # Use hybrid strategy (mood cluster + popularity)
            songs = self._hybrid_recommendations(mood, limit)
            strategy = "cold_start_hybrid"
        else:
            # Use pure popularity baseline
            songs = self._popularity_baseline(limit)
            strategy = "cold_start_popularity"
        
        return songs, strategy, personalization_weight
    
    def _popularity_baseline(self, limit: int) -> List[ColdStartSong]:
        """
        Get recommendations based on global popularity.
        
        Ranks songs by: (likes - 0.5 * dislikes) with time decay.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Try to get songs with popularity metrics
            cursor.execute("""
                SELECT 
                    song_id, name, artist, genre, moods as mood,
                    COALESCE(popularity, 50) as popularity,
                    COALESCE(like_count, 0) as like_count
                FROM songs
                ORDER BY popularity DESC, like_count DESC
                LIMIT ?
            """, (limit * 2,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return []
            
            songs = []
            for i, row in enumerate(rows[:limit]):
                # Score decays by position
                score = 1.0 - (i * 0.05)
                
                songs.append(ColdStartSong(
                    song_id=row["song_id"],
                    name=row["name"],
                    artist=row["artist"],
                    genre=row["genre"],
                    mood=row["mood"],
                    score=max(0.1, score),
                    strategy="popularity_baseline",
                    explanation="Trending song that many users love",
                ))
            
            return songs
            
        except Exception as e:
            print(f"Error in popularity baseline: {e}")
            return []
    
    def _mood_cluster_bootstrap(
        self,
        mood: str,
        limit: int,
        diversity_factor: float = 0.3,
    ) -> List[ColdStartSong]:
        """
        Get recommendations from mood cluster.
        
        Retrieves songs near the mood centroid in VA-space.
        """
        # Get mood centroid
        if mood.lower() not in self.MOOD_CENTROIDS:
            centroid = (0.0, 0.0)
            effective_mood = "neutral"
        else:
            centroid = self.MOOD_CENTROIDS[mood.lower()]
            effective_mood = mood.lower()
        
        va_threshold = 0.5  # Distance threshold in VA-space
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get songs matching mood or near VA centroid
            cursor.execute("""
                SELECT 
                    song_id, name, artist, genre, moods as mood,
                    COALESCE(valence, 0) as valence,
                    COALESCE(energy, 0) as energy
                FROM songs
                WHERE moods LIKE ? OR moods IS NULL
                LIMIT ?
            """, (f"%{effective_mood}%", limit * 3))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return []
            
            # Calculate VA distance and score
            candidates = []
            for row in rows:
                valence = float(row["valence"])
                energy = float(row["energy"])
                va_distance = math.sqrt(
                    (valence - centroid[0]) ** 2 +
                    (energy - centroid[1]) ** 2
                )
                
                if va_distance < va_threshold or row["mood"]:
                    # Score inversely proportional to distance
                    score = max(0.1, 1.0 - va_distance)
                    candidates.append((row, score, va_distance))
            
            # Sort by score
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Apply diversity sampling
            songs = self._diversity_sample(candidates, limit, diversity_factor, effective_mood)
            
            return songs
            
        except Exception as e:
            print(f"Error in mood cluster bootstrap: {e}")
            return []
    
    def _diversity_sample(
        self,
        candidates: List[Tuple[Any, float, float]],
        k: int,
        diversity: float,
        mood: str,
    ) -> List[ColdStartSong]:
        """
        Sample k songs maximizing diversity using greedy maximin.
        """
        if not candidates:
            return []
        
        if len(candidates) <= k:
            return [
                ColdStartSong(
                    song_id=row["song_id"],
                    name=row["name"],
                    artist=row["artist"],
                    genre=row["genre"],
                    mood=row["mood"],
                    score=score,
                    strategy="mood_cluster_bootstrap",
                    explanation=f"A {mood} track that matches your current mood",
                )
                for row, score, _ in candidates
            ]
        
        # Start with highest scored
        selected = [candidates[0]]
        remaining = candidates[1:]
        seen_artists = {candidates[0][0]["artist"]}
        
        while len(selected) < k and remaining:
            best_idx = 0
            best_diversity_score = -1
            
            for i, (row, score, _) in enumerate(remaining):
                # Diversity bonus for different artists
                artist = row["artist"]
                artist_bonus = 0.2 if artist not in seen_artists else 0.0
                
                diversity_score = score * (1 - diversity) + artist_bonus * diversity
                
                if diversity_score > best_diversity_score:
                    best_diversity_score = diversity_score
                    best_idx = i
            
            selected.append(remaining.pop(best_idx))
            seen_artists.add(selected[-1][0]["artist"])
        
        return [
            ColdStartSong(
                song_id=row["song_id"],
                name=row["name"],
                artist=row["artist"],
                genre=row["genre"],
                mood=row["mood"],
                score=score,
                strategy="mood_cluster_bootstrap",
                explanation=f"A {mood} track that matches your current mood",
            )
            for row, score, _ in selected
        ]
    
    def _hybrid_recommendations(
        self,
        mood: str,
        limit: int,
        cluster_weight: float = 0.6,
        popularity_weight: float = 0.4,
    ) -> List[ColdStartSong]:
        """
        Hybrid recommendations combining mood cluster and popularity.
        """
        # Get recommendations from both sources
        n_cluster = int(limit * cluster_weight)
        n_popular = limit - n_cluster
        
        cluster_songs = self._mood_cluster_bootstrap(mood, n_cluster)
        popular_songs = self._popularity_baseline(n_popular)
        
        # Update explanations for hybrid
        for song in popular_songs:
            song.strategy = "cold_start_hybrid"
            song.explanation = f"Popular {mood} track that others have enjoyed"
        
        for song in cluster_songs:
            song.strategy = "cold_start_hybrid"
        
        # Interleave for variety
        result = []
        cluster_iter = iter(cluster_songs)
        popular_iter = iter(popular_songs)
        
        while len(result) < limit:
            try:
                result.append(next(cluster_iter))
            except StopIteration:
                pass
            
            if len(result) < limit:
                try:
                    result.append(next(popular_iter))
                except StopIteration:
                    pass
            
            if not cluster_songs and not popular_songs:
                break
        
        # Recalculate scores by position
        for i, song in enumerate(result):
            song.score = 1.0 - (i * 0.05)
        
        return result[:limit]
    
    def handle_new_song(
        self,
        song_id: int,
        song_features: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Score a new song without user feedback.
        
        Uses content-based features only.
        """
        score = 0.0
        
        # Content similarity to user profile (if exists)
        if user_profile and user_profile.get("avg_liked_features"):
            # Simple feature matching
            avg_features = user_profile["avg_liked_features"]
            
            valence_diff = abs(
                song_features.get("valence", 0) - avg_features.get("valence", 0)
            )
            energy_diff = abs(
                song_features.get("energy", 0) - avg_features.get("energy", 0)
            )
            
            content_sim = max(0, 1.0 - (valence_diff + energy_diff) / 2)
            score += 0.5 * content_sim
        
        # Artist popularity boost
        artist_popularity = song_features.get("artist_popularity", 0.5)
        score += 0.3 * artist_popularity
        
        # Genre match
        if user_profile and song_features.get("genre") in user_profile.get("preferred_genres", []):
            score += 0.2
        
        # Exploration bonus for new songs
        score += 0.1
        
        return min(1.0, score)


class ColdStartTransitionManager:
    """
    Manages gradual transition from cold start to personalized recommendations.
    """
    
    def __init__(self, cold_start_handler: ColdStartHandler):
        self.handler = cold_start_handler
    
    def blend_recommendations(
        self,
        user_id: int,
        cold_start_songs: List[ColdStartSong],
        personalized_songs: List[Any],
        limit: int = 10,
    ) -> Tuple[List[Any], Dict[str, float]]:
        """
        Blend cold start and personalized recommendations.
        
        Args:
            user_id: User ID
            cold_start_songs: Recommendations from cold start
            personalized_songs: Recommendations from personalization engine
            limit: Total number to return
            
        Returns:
            Tuple of (blended_songs, blend_weights)
        """
        pw = self.handler.get_personalization_weight(user_id)
        
        blend_weights = {
            "personalization_weight": pw,
            "cold_start_weight": 1.0 - pw,
        }
        
        if pw >= 1.0:
            # Full personalization
            return personalized_songs[:limit], blend_weights
        
        if pw <= 0.0:
            # Full cold start
            return cold_start_songs[:limit], blend_weights
        
        # Blend based on weights
        n_personalized = int(limit * pw)
        n_cold_start = limit - n_personalized
        
        blended = []
        blended.extend(personalized_songs[:n_personalized])
        
        # Add cold start songs (as dicts for compatibility)
        for song in cold_start_songs[:n_cold_start]:
            blended.append(song.to_dict())
        
        return blended, blend_weights


# Global cold start handler instance
_cold_start_handler: Optional[ColdStartHandler] = None


def get_cold_start_handler(db_path: Optional[str] = None) -> ColdStartHandler:
    """Get or create the global cold start handler."""
    global _cold_start_handler
    if _cold_start_handler is None:
        _cold_start_handler = ColdStartHandler(db_path)
    return _cold_start_handler
