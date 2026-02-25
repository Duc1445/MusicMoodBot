"""
=============================================================================
HYBRID RANKING ENGINE
=============================================================================

Production-level multi-factor ranking system for music recommendations.

The ranking formula:
    final_score = Σ(wi * component_i)

Components:
1. Mood Similarity (categorical + VA space)
2. Intensity Match (distance-based)
3. User Preference Weight (learned from feedback)
4. Recency Penalty (diminishing returns for repeated songs)
5. Diversity Penalty (avoid clustering same artist/genre)
6. Popularity Boost (social proof)

Mathematical Foundation:
- Each component is normalized to [0, 1]
- Weights are configurable and sum to 1.0
- Explanations generated for each recommendation

Author: MusicMoodBot Team
Version: 3.1.0
=============================================================================
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class RankingConfig:
    """Configuration for the hybrid ranking engine."""
    
    # Component weights (must sum to 1.0)
    w_mood_similarity: float = 0.30      # w1: Mood matching
    w_intensity_match: float = 0.15      # w2: Intensity matching
    w_user_preference: float = 0.25      # w3: Personalization
    w_recency_penalty: float = 0.10      # w4: Novelty
    w_diversity_penalty: float = 0.10    # w5: Variety
    w_popularity_boost: float = 0.10     # w6: Social proof
    
    # Component parameters
    intensity_gaussian_sigma: float = 0.2  # For intensity match
    recency_decay_days: int = 7            # Half-life for recency
    diversity_window: int = 5              # Songs to consider for diversity
    popularity_percentile_cap: float = 0.95  # Cap for popularity normalization
    
    # VA space parameters
    va_space_weight: float = 0.6  # Weight of VA similarity vs categorical
    
    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = (
            self.w_mood_similarity +
            self.w_intensity_match +
            self.w_user_preference +
            self.w_recency_penalty +
            self.w_diversity_penalty +
            self.w_popularity_boost
        )
        if not (0.99 <= total <= 1.01):
            logger.warning(f"Ranking weights sum to {total}, expected 1.0")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ScoringComponents:
    """
    Individual scoring components for a song.
    
    Each component is normalized to [0, 1].
    """
    mood_similarity: float = 0.0
    intensity_match: float = 0.0
    user_preference: float = 0.0
    recency_penalty: float = 0.0
    diversity_penalty: float = 0.0
    popularity_boost: float = 0.0
    
    # Sub-components for detailed analysis
    categorical_mood_score: float = 0.0
    va_space_score: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'mood_similarity': round(self.mood_similarity, 4),
            'intensity_match': round(self.intensity_match, 4),
            'user_preference': round(self.user_preference, 4),
            'recency_penalty': round(self.recency_penalty, 4),
            'diversity_penalty': round(self.diversity_penalty, 4),
            'popularity_boost': round(self.popularity_boost, 4),
            'categorical_mood_score': round(self.categorical_mood_score, 4),
            'va_space_score': round(self.va_space_score, 4),
        }


@dataclass
class RankingExplanation:
    """
    Human-readable explanation for why a song was recommended.
    
    Provides transparency into the ranking decision.
    """
    song_id: int
    song_name: str
    artist: str
    
    primary_reason: str
    secondary_reasons: List[str] = field(default_factory=list)
    
    # Score breakdown
    final_score: float = 0.0
    components: ScoringComponents = field(default_factory=ScoringComponents)
    
    # Contribution analysis
    top_contributor: str = ""
    contribution_percentages: Dict[str, float] = field(default_factory=dict)
    
    def to_natural_language(self, lang: str = 'vi') -> str:
        """Generate natural language explanation."""
        if lang == 'vi':
            return self._generate_vietnamese()
        return self._generate_english()
    
    def _generate_vietnamese(self) -> str:
        """Vietnamese explanation."""
        reasons = [self.primary_reason]
        if self.secondary_reasons:
            reasons.extend(self.secondary_reasons[:2])
        
        text = f"Gợi ý \"{self.song_name}\" của {self.artist} vì: "
        text += "; ".join(reasons) + "."
        
        return text
    
    def _generate_english(self) -> str:
        """English explanation."""
        reasons = [self.primary_reason]
        if self.secondary_reasons:
            reasons.extend(self.secondary_reasons[:2])
        
        text = f"Recommended \"{self.song_name}\" by {self.artist} because: "
        text += "; ".join(reasons) + "."
        
        return text


@dataclass
class RankingResult:
    """Result of ranking a single song."""
    song_id: int
    song_data: Dict[str, Any]
    final_score: float
    components: ScoringComponents
    explanation: RankingExplanation
    rank: int = 0


# =============================================================================
# MOOD MAPPING
# =============================================================================

# Categorical mood to valence-arousal (VA) coordinates
# Valence: -1 (negative) to +1 (positive)
# Arousal: 0 (low energy) to 1 (high energy)
MOOD_VA_COORDINATES = {
    'happy': {'valence': 0.8, 'arousal': 0.7},
    'sad': {'valence': -0.7, 'arousal': 0.2},
    'energetic': {'valence': 0.5, 'arousal': 0.9},
    'calm': {'valence': 0.3, 'arousal': 0.2},
    'angry': {'valence': -0.8, 'arousal': 0.9},
    'romantic': {'valence': 0.6, 'arousal': 0.4},
    'nostalgic': {'valence': 0.1, 'arousal': 0.3},
    'anxious': {'valence': -0.5, 'arousal': 0.7},
    'stress': {'valence': -0.4, 'arousal': 0.6},
    'chill': {'valence': 0.4, 'arousal': 0.3},
    'excited': {'valence': 0.7, 'arousal': 0.85},
    'melancholic': {'valence': -0.3, 'arousal': 0.25},
}

# Vietnamese mood mapping
MOOD_VI_TO_EN = {
    'Vui': 'happy',
    'Buồn': 'sad',
    'Năng lượng': 'energetic',
    'Bình yên': 'calm',
    'Tức giận': 'angry',
    'Lãng mạn': 'romantic',
    'Hoài niệm': 'nostalgic',
    'Lo lắng': 'anxious',
    'Suy tư': 'stress',
    'Chill': 'chill',
    'Phấn khích': 'excited',
    'U sầu': 'melancholic',
}


# =============================================================================
# HYBRID RANKING ENGINE
# =============================================================================

class HybridRankingEngine:
    """
    Production-level hybrid music recommendation ranking engine.
    
    Implements the weighted multi-factor ranking formula:
    
        final_score = w1 * mood_similarity 
                    + w2 * intensity_match 
                    + w3 * user_preference 
                    + w4 * recency_penalty 
                    + w5 * diversity_penalty 
                    + w6 * popularity_boost
    
    Usage:
        engine = HybridRankingEngine()
        
        results = engine.rank_songs(
            candidates=songs,
            target_mood='sad',
            target_intensity=0.7,
            target_valence=-0.6,
            target_arousal=0.3,
            user_prefs=user_preferences,
            listening_history=recent_songs,
            limit=10
        )
    """
    
    def __init__(self, config: RankingConfig = None):
        """
        Initialize ranking engine.
        
        Args:
            config: Ranking configuration (uses defaults if None)
        """
        self.config = config or RankingConfig()
        
        # Cache for popularity statistics
        self._popularity_stats: Dict[str, float] = {}
        self._popularity_cache_time: Optional[datetime] = None
        self._pop_cache_ttl = timedelta(hours=1)
    
    # =========================================================================
    # MAIN RANKING METHOD
    # =========================================================================
    
    def rank_songs(
        self,
        candidates: List[Dict[str, Any]],
        target_mood: str,
        target_intensity: float = 0.5,
        target_valence: float = None,
        target_arousal: float = None,
        user_prefs: Dict[str, Any] = None,
        listening_history: List[Dict[str, Any]] = None,
        already_recommended: List[int] = None,
        limit: int = 10
    ) -> List[RankingResult]:
        """
        Rank candidate songs using the hybrid multi-factor formula.
        
        Args:
            candidates: List of song dicts from database
            target_mood: Target mood category (e.g., 'sad', 'happy')
            target_intensity: Target intensity [0, 1]
            target_valence: Target valence [-1, 1] (optional)
            target_arousal: Target arousal [0, 1] (optional)
            user_prefs: User preference weights
            listening_history: Recent listening history for recency
            already_recommended: Song IDs already in current playlist
            limit: Maximum results to return
            
        Returns:
            List of RankingResult sorted by final_score descending
        """
        if not candidates:
            return []
        
        # Normalize inputs
        target_mood = self._normalize_mood(target_mood)
        user_prefs = user_prefs or {}
        listening_history = listening_history or []
        already_recommended = already_recommended or []
        
        # Infer VA coordinates if not provided
        if target_valence is None or target_arousal is None:
            va = MOOD_VA_COORDINATES.get(target_mood, {'valence': 0, 'arousal': 0.5})
            target_valence = target_valence if target_valence is not None else va['valence']
            target_arousal = target_arousal if target_arousal is not None else va['arousal']
        
        # Compute popularity statistics
        self._update_popularity_stats(candidates)
        
        # Build listening history lookup
        history_map = self._build_history_map(listening_history)
        
        # Score each candidate
        results = []
        for i, song in enumerate(candidates):
            try:
                result = self._score_song(
                    song=song,
                    target_mood=target_mood,
                    target_intensity=target_intensity,
                    target_valence=target_valence,
                    target_arousal=target_arousal,
                    user_prefs=user_prefs,
                    history_map=history_map,
                    preceding_songs=already_recommended + [r.song_id for r in results[-self.config.diversity_window:]],
                    all_candidates=candidates
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Error scoring song {song.get('song_id')}: {e}")
        
        # Sort by final score
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Assign ranks
        for i, result in enumerate(results):
            result.rank = i + 1
        
        return results[:limit]
    
    # =========================================================================
    # SCORING IMPLEMENTATION
    # =========================================================================
    
    def _score_song(
        self,
        song: Dict[str, Any],
        target_mood: str,
        target_intensity: float,
        target_valence: float,
        target_arousal: float,
        user_prefs: Dict[str, Any],
        history_map: Dict[int, datetime],
        preceding_songs: List[int],
        all_candidates: List[Dict]
    ) -> RankingResult:
        """Score a single song using all components."""
        
        components = ScoringComponents()
        
        # Component 1: Mood Similarity
        components.mood_similarity, components.categorical_mood_score, components.va_space_score = \
            self._compute_mood_similarity(
                song, target_mood, target_valence, target_arousal
            )
        
        # Component 2: Intensity Match
        components.intensity_match = self._compute_intensity_match(
            song, target_intensity
        )
        
        # Component 3: User Preference Weight
        components.user_preference = self._compute_user_preference(
            song, user_prefs
        )
        
        # Component 4: Recency Penalty
        components.recency_penalty = self._compute_recency_penalty(
            song, history_map
        )
        
        # Component 5: Diversity Penalty
        components.diversity_penalty = self._compute_diversity_penalty(
            song, preceding_songs, all_candidates
        )
        
        # Component 6: Popularity Boost
        components.popularity_boost = self._compute_popularity_boost(song)
        
        # Compute final weighted score
        final_score = (
            self.config.w_mood_similarity * components.mood_similarity +
            self.config.w_intensity_match * components.intensity_match +
            self.config.w_user_preference * components.user_preference +
            self.config.w_recency_penalty * components.recency_penalty +
            self.config.w_diversity_penalty * components.diversity_penalty +
            self.config.w_popularity_boost * components.popularity_boost
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            song, final_score, components, target_mood, target_intensity
        )
        
        return RankingResult(
            song_id=song.get('song_id', 0),
            song_data=song,
            final_score=final_score,
            components=components,
            explanation=explanation
        )
    
    # =========================================================================
    # COMPONENT COMPUTATIONS
    # =========================================================================
    
    def _compute_mood_similarity(
        self,
        song: Dict[str, Any],
        target_mood: str,
        target_valence: float,
        target_arousal: float
    ) -> Tuple[float, float, float]:
        """
        Compute mood similarity combining categorical and VA space.
        
        Formula:
            mood_similarity = (1 - va_weight) * categorical_score + va_weight * va_score
        
        Where:
            categorical_score = 1.0 if exact match, 0.5 if related, 0.0 otherwise
            va_score = 1 - normalized_distance in VA space
        
        Returns:
            Tuple of (combined_score, categorical_score, va_score)
        """
        # Categorical matching
        song_mood = self._normalize_mood(song.get('mood', ''))
        
        if song_mood == target_mood:
            categorical_score = 1.0
        elif self._are_moods_related(song_mood, target_mood):
            categorical_score = 0.6
        else:
            categorical_score = 0.2
        
        # VA space matching
        # Get song's VA coordinates
        song_valence = song.get('valence_score') or song.get('valence', 50)
        song_arousal = song.get('arousal_score') or song.get('energy', 50)
        
        # Normalize to [-1, 1] for valence and [0, 1] for arousal
        if isinstance(song_valence, (int, float)) and song_valence > 1:
            song_valence = (song_valence - 50) / 50  # 0-100 → -1 to 1
        if isinstance(song_arousal, (int, float)) and song_arousal > 1:
            song_arousal = song_arousal / 100  # 0-100 → 0 to 1
        
        # Euclidean distance in VA space
        # Maximum possible distance = sqrt(2^2 + 1^2) = sqrt(5) ≈ 2.236
        distance = math.sqrt(
            (song_valence - target_valence) ** 2 +
            (song_arousal - target_arousal) ** 2
        )
        max_distance = math.sqrt(4 + 1)  # sqrt(2^2 + 1^2)
        va_score = 1.0 - (distance / max_distance)
        va_score = max(0.0, va_score)
        
        # Combined score
        combined = (
            (1 - self.config.va_space_weight) * categorical_score +
            self.config.va_space_weight * va_score
        )
        
        return combined, categorical_score, va_score
    
    def _compute_intensity_match(
        self,
        song: Dict[str, Any],
        target_intensity: float
    ) -> float:
        """
        Compute intensity match using Gaussian kernel.
        
        Formula:
            score = exp(-((song_intensity - target_intensity)^2) / (2 * σ^2))
        
        This gives a smooth bell curve centered on target intensity.
        """
        # Get song intensity
        song_intensity = song.get('intensity', 0.5)
        
        # Also consider energy as intensity proxy
        song_energy = song.get('energy', 50)
        if isinstance(song_energy, (int, float)) and song_energy > 1:
            song_energy = song_energy / 100  # Normalize
        
        # Use energy-based intensity if explicit intensity not available
        if song_intensity == 0.5 and song_energy != 0.5:
            song_intensity = song_energy
        
        # Gaussian kernel
        sigma = self.config.intensity_gaussian_sigma
        diff = song_intensity - target_intensity
        score = math.exp(-(diff ** 2) / (2 * sigma ** 2))
        
        return score
    
    def _compute_user_preference(
        self,
        song: Dict[str, Any],
        user_prefs: Dict[str, Any]
    ) -> float:
        """
        Compute user preference score from learned weights.
        
        Formula:
            score = Π(preference_weights) normalized to [0, 1]
        
        Considers:
        - Mood preferences
        - Genre preferences
        - Artist preferences
        """
        if not user_prefs:
            return 0.5  # Neutral preference
        
        score_factors = []
        
        # Mood preference
        song_mood = self._normalize_mood(song.get('mood', ''))
        mood_prefs = user_prefs.get('mood', {})
        if song_mood and song_mood in mood_prefs:
            # Weights are stored as multipliers, normalize to [0, 1]
            weight = mood_prefs[song_mood]
            score_factors.append(self._normalize_weight(weight))
        
        # Genre preference
        song_genre = song.get('genre', '')
        genre_prefs = user_prefs.get('genre', {})
        if song_genre and song_genre in genre_prefs:
            weight = genre_prefs[song_genre]
            score_factors.append(self._normalize_weight(weight))
        
        # Artist preference
        song_artist = song.get('artist', '')
        artist_prefs = user_prefs.get('artist', {})
        if song_artist and song_artist in artist_prefs:
            weight = artist_prefs[song_artist]
            score_factors.append(self._normalize_weight(weight))
        
        if not score_factors:
            return 0.5
        
        # Geometric mean of factors
        product = 1.0
        for f in score_factors:
            product *= f
        
        return product ** (1 / len(score_factors))
    
    def _compute_recency_penalty(
        self,
        song: Dict[str, Any],
        history_map: Dict[int, datetime]
    ) -> float:
        """
        Compute recency penalty to avoid repetition.
        
        Formula:
            score = 1 - exp(-days_since_last / half_life)
        
        Returns higher scores for songs not recently played.
        """
        song_id = song.get('song_id', 0)
        
        if song_id not in history_map:
            return 1.0  # Never played → maximum novelty
        
        last_played = history_map[song_id]
        days_since = (datetime.now() - last_played).total_seconds() / 86400
        
        # Exponential decay
        half_life = self.config.recency_decay_days
        score = 1.0 - math.exp(-days_since / half_life)
        
        return score
    
    def _compute_diversity_penalty(
        self,
        song: Dict[str, Any],
        preceding_songs: List[int],
        all_candidates: List[Dict]
    ) -> float:
        """
        Compute diversity penalty to ensure variety.
        
        Formula:
            penalty = 1 - (same_artist_count + same_genre_count * 0.5) / window_size
        
        Returns higher scores for songs different from recently recommended.
        """
        if not preceding_songs:
            return 1.0  # No context → maximum diversity
        
        # Build lookup for preceding songs
        preceding_lookup = {}
        for candidate in all_candidates:
            if candidate.get('song_id') in preceding_songs:
                preceding_lookup[candidate['song_id']] = candidate
        
        song_artist = song.get('artist', '')
        song_genre = song.get('genre', '')
        
        same_artist = 0
        same_genre = 0
        
        for song_id in preceding_songs[-self.config.diversity_window:]:
            if song_id in preceding_lookup:
                other = preceding_lookup[song_id]
                if other.get('artist') == song_artist:
                    same_artist += 1
                if other.get('genre') == song_genre:
                    same_genre += 1
        
        window = min(len(preceding_songs), self.config.diversity_window)
        if window == 0:
            return 1.0
        
        penalty_raw = (same_artist + same_genre * 0.5) / window
        score = 1.0 - min(penalty_raw, 1.0)
        
        return score
    
    def _compute_popularity_boost(self, song: Dict[str, Any]) -> float:
        """
        Compute popularity boost for social proof.
        
        Formula:
            score = min(percentile_rank / cap, 1.0)
        
        Uses average ratings and play counts.
        """
        # Get popularity metrics
        avg_rating = song.get('avg_rating', 0) or 0
        play_count = song.get('play_count', 0) or song.get('listened_count', 0) or 0
        
        # Normalize rating (assume 0-5 scale)
        rating_score = avg_rating / 5.0 if avg_rating else 0.5
        
        # Normalize play count using cached stats
        max_plays = self._popularity_stats.get('max_plays', 1000)
        plays_score = min(play_count / max_plays, 1.0) if max_plays > 0 else 0.5
        
        # Combined popularity
        score = 0.6 * rating_score + 0.4 * plays_score
        
        # Apply cap
        return min(score / self.config.popularity_percentile_cap, 1.0)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _normalize_mood(self, mood: str) -> str:
        """Normalize mood to English lowercase."""
        if not mood:
            return ''
        mood = mood.strip()
        return MOOD_VI_TO_EN.get(mood, mood.lower())
    
    def _are_moods_related(self, mood1: str, mood2: str) -> bool:
        """Check if two moods are related."""
        related_groups = [
            {'happy', 'excited', 'energetic'},
            {'sad', 'melancholic', 'nostalgic'},
            {'calm', 'chill', 'romantic'},
            {'angry', 'anxious', 'stress'},
        ]
        
        for group in related_groups:
            if mood1 in group and mood2 in group:
                return True
        return False
    
    def _normalize_weight(self, weight: float) -> float:
        """Normalize preference weight to [0, 1]."""
        # Weights are typically in [0.5, 2.0] range
        # Map to [0, 1]: 0.5 → 0, 1.0 → 0.5, 2.0 → 1.0
        return min(max((weight - 0.5) / 1.5, 0.0), 1.0)
    
    def _build_history_map(self, history: List[Dict]) -> Dict[int, datetime]:
        """Build song_id → last_played mapping."""
        history_map = {}
        for entry in history:
            song_id = entry.get('song_id')
            played_at = entry.get('played_at') or entry.get('listened_at')
            
            if song_id and played_at:
                if isinstance(played_at, str):
                    try:
                        played_at = datetime.fromisoformat(played_at)
                    except:
                        continue
                
                if song_id not in history_map or played_at > history_map[song_id]:
                    history_map[song_id] = played_at
        
        return history_map
    
    def _update_popularity_stats(self, candidates: List[Dict]):
        """Update cached popularity statistics."""
        now = datetime.now()
        if (self._popularity_cache_time and 
            now - self._popularity_cache_time < self._pop_cache_ttl):
            return
        
        play_counts = [
            c.get('play_count', 0) or c.get('listened_count', 0) or 0
            for c in candidates
        ]
        
        self._popularity_stats = {
            'max_plays': max(play_counts) if play_counts else 1000,
            'avg_plays': sum(play_counts) / len(play_counts) if play_counts else 500,
        }
        self._popularity_cache_time = now
    
    def _generate_explanation(
        self,
        song: Dict[str, Any],
        final_score: float,
        components: ScoringComponents,
        target_mood: str,
        target_intensity: float
    ) -> RankingExplanation:
        """Generate human-readable explanation."""
        
        # Calculate contributions
        contributions = {
            'mood': self.config.w_mood_similarity * components.mood_similarity,
            'intensity': self.config.w_intensity_match * components.intensity_match,
            'preference': self.config.w_user_preference * components.user_preference,
            'novelty': self.config.w_recency_penalty * components.recency_penalty,
            'diversity': self.config.w_diversity_penalty * components.diversity_penalty,
            'popularity': self.config.w_popularity_boost * components.popularity_boost,
        }
        
        # Find top contributor
        top_key = max(contributions, key=contributions.get)
        
        # Calculate percentages
        total = sum(contributions.values())
        percentages = {
            k: (v / total * 100) if total > 0 else 0
            for k, v in contributions.items()
        }
        
        # Generate reasons
        reasons = []
        
        if components.mood_similarity > 0.7:
            reasons.append(f"phù hợp tâm trạng {target_mood}")
        
        if components.intensity_match > 0.8:
            intensity_word = 'nhẹ nhàng' if target_intensity < 0.4 else ('mạnh mẽ' if target_intensity > 0.7 else 'vừa phải')
            reasons.append(f"cường độ {intensity_word}")
        
        if components.user_preference > 0.7:
            reasons.append("phù hợp sở thích của bạn")
        
        if components.recency_penalty > 0.9:
            reasons.append("bài hát mới lạ")
        
        if components.diversity_penalty > 0.8:
            reasons.append("tạo đa dạng playlist")
        
        if components.popularity_boost > 0.7:
            reasons.append("được nhiều người yêu thích")
        
        # Fallback reason
        if not reasons:
            reasons.append("điểm tổng hợp cao")
        
        return RankingExplanation(
            song_id=song.get('song_id', 0),
            song_name=song.get('song_name') or song.get('name', 'Unknown'),
            artist=song.get('artist', 'Unknown'),
            primary_reason=reasons[0] if reasons else '',
            secondary_reasons=reasons[1:3] if len(reasons) > 1 else [],
            final_score=final_score,
            components=components,
            top_contributor=top_key,
            contribution_percentages=percentages
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_ranking_engine(config: RankingConfig = None) -> HybridRankingEngine:
    """Create a HybridRankingEngine instance."""
    return HybridRankingEngine(config)
