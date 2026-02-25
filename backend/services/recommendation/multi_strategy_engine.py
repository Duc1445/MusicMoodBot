"""
=============================================================================
MULTI-STRATEGY RECOMMENDATION ENGINE
=============================================================================

Advanced recommendation engine combining multiple strategies with
exploration/exploitation balancing.

Strategies:
===========
1. Emotion-Based Matching    - VA space similarity
2. Content Similarity        - Genre, artist, audio features
3. Collaborative Filtering   - User preference patterns
4. Diversity Injection       - Prevent filter bubbles
5. Exploration Component     - Discover new content

Balancing Algorithm:
===================
Uses Thompson Sampling with contextual bandits for dynamic strategy
weight selection based on user feedback history.

Formula:
    final_score = Σ(strategy_weight_i * strategy_score_i)
    
    where strategy_weight is determined by:
    - Historical performance (exploitation)
    - Uncertainty bonus (exploration)
    - Context modifiers (user state, time, session)

Author: MusicMoodBot Team
Version: 4.0.0
=============================================================================
"""

from __future__ import annotations

import math
import random
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class StrategyConfig:
    """Configuration for multi-strategy engine."""
    
    # Base strategy weights (prior)
    emotion_weight: float = 0.30
    content_weight: float = 0.25
    collaborative_weight: float = 0.20
    diversity_weight: float = 0.15
    exploration_weight: float = 0.10
    
    # Exploration parameters
    exploration_rate: float = 0.15  # ε for ε-greedy
    ucb_confidence: float = 2.0     # c for UCB1
    thompson_alpha: float = 1.0     # Beta distribution alpha
    thompson_beta: float = 1.0      # Beta distribution beta
    
    # Diversity parameters
    diversity_penalty_decay: float = 0.8  # Per-song decay in recent window
    diversity_window_size: int = 10
    min_diversity_score: float = 0.3
    
    # Context modifiers
    time_of_day_modifier: bool = True
    session_length_modifier: bool = True
    mood_intensity_modifier: bool = True
    
    # Learning parameters
    learning_rate: float = 0.1
    weight_decay: float = 0.01
    min_weight: float = 0.05
    max_weight: float = 0.50
    
    def validate(self):
        """Validate configuration."""
        total = (
            self.emotion_weight + self.content_weight +
            self.collaborative_weight + self.diversity_weight +
            self.exploration_weight
        )
        if not (0.99 <= total <= 1.01):
            logger.warning(f"Strategy weights sum to {total}, normalizing...")
            self._normalize_weights(total)
    
    def _normalize_weights(self, total: float):
        """Normalize weights to sum to 1.0."""
        if total > 0:
            self.emotion_weight /= total
            self.content_weight /= total
            self.collaborative_weight /= total
            self.diversity_weight /= total
            self.exploration_weight /= total


class StrategyType(Enum):
    """Types of recommendation strategies."""
    EMOTION = "emotion"
    CONTENT = "content"
    COLLABORATIVE = "collaborative"
    DIVERSITY = "diversity"
    EXPLORATION = "exploration"


class ExplorationMethod(Enum):
    """Methods for exploration/exploitation balancing."""
    EPSILON_GREEDY = auto()
    UCB1 = auto()
    THOMPSON_SAMPLING = auto()
    SOFTMAX = auto()


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class StrategyScore:
    """Score from a single strategy."""
    strategy: StrategyType
    score: float  # [0, 1]
    confidence: float  # [0, 1]
    components: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""


@dataclass
class StrategyPerformance:
    """Performance tracking for a strategy."""
    strategy: StrategyType
    successes: int = 0  # Positive feedback
    failures: int = 0   # Negative feedback
    total_pulls: int = 0
    cumulative_reward: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.successes + self.failures
        return self.successes / total if total > 0 else 0.5
    
    @property
    def average_reward(self) -> float:
        """Calculate average reward."""
        return self.cumulative_reward / self.total_pulls if self.total_pulls > 0 else 0.0


@dataclass
class RecommendationContext:
    """Context for recommendation generation."""
    user_id: int
    target_mood: str
    target_valence: float = 0.0
    target_arousal: float = 0.0
    target_intensity: float = 0.5
    
    session_id: Optional[str] = None
    session_turn: int = 0
    session_songs: List[int] = field(default_factory=list)
    
    time_of_day: Optional[str] = None  # morning, afternoon, evening, night
    day_of_week: Optional[int] = None  # 0-6
    
    user_history: List[Dict] = field(default_factory=list)
    user_preferences: Dict[str, float] = field(default_factory=dict)
    
    explicit_constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CandidateSong:
    """Song candidate with multi-strategy scores."""
    song_id: int
    song_data: Dict[str, Any]
    
    strategy_scores: Dict[StrategyType, StrategyScore] = field(default_factory=dict)
    final_score: float = 0.0
    final_confidence: float = 0.0
    
    explanation_components: List[str] = field(default_factory=list)
    selected_strategy: Optional[StrategyType] = None


@dataclass 
class RecommendationResult:
    """Result of recommendation generation."""
    songs: List[CandidateSong]
    strategy_weights_used: Dict[StrategyType, float]
    exploration_method: ExplorationMethod
    context_modifiers: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# BASE STRATEGY
# =============================================================================

class RecommendationStrategy(ABC):
    """Abstract base class for recommendation strategies."""
    
    strategy_type: StrategyType
    
    @abstractmethod
    def score(
        self,
        song: Dict[str, Any],
        context: RecommendationContext
    ) -> StrategyScore:
        """
        Score a song using this strategy.
        
        Args:
            song: Song data dictionary
            context: Recommendation context
            
        Returns:
            StrategyScore with score in [0, 1]
        """
        pass
    
    @abstractmethod
    def explain(
        self,
        song: Dict[str, Any],
        score: StrategyScore,
        context: RecommendationContext
    ) -> str:
        """Generate natural language explanation for this strategy's contribution."""
        pass


# =============================================================================
# EMOTION-BASED STRATEGY
# =============================================================================

class EmotionStrategy(RecommendationStrategy):
    """
    Emotion-based matching using Valence-Arousal space.
    
    Scoring Formula:
        emotion_score = 1 - (euclidean_distance / max_distance)
        
    Where:
        euclidean_distance = sqrt((v_song - v_target)² + (a_song - a_target)²)
        max_distance = sqrt(8) ≈ 2.83 (diagonal of [-1,1] × [-1,1] space)
    """
    
    strategy_type = StrategyType.EMOTION
    
    # Mood to VA mapping
    MOOD_VA_MAP = {
        "happy": (0.8, 0.6),
        "sad": (-0.7, -0.3),
        "angry": (-0.6, 0.8),
        "calm": (0.5, -0.5),
        "excited": (0.7, 0.9),
        "peaceful": (0.6, -0.7),
        "anxious": (-0.3, 0.7),
        "melancholy": (-0.5, -0.4),
        "romantic": (0.6, 0.2),
        "energetic": (0.5, 0.9),
        "nostalgic": (0.1, -0.2),
        "neutral": (0.0, 0.0),
    }
    
    MAX_DISTANCE = math.sqrt(8)  # Diagonal of 2x2 space
    
    def score(
        self,
        song: Dict[str, Any],
        context: RecommendationContext
    ) -> StrategyScore:
        """Score based on emotional distance in VA space."""
        
        # Get song's VA coordinates
        song_valence = song.get('valence', 0.0)
        song_arousal = song.get('arousal', song.get('energy', 0.0))
        
        # If song has categorical mood, use it as fallback
        if song_valence == 0.0 and song_arousal == 0.0:
            song_mood = song.get('mood', 'neutral').lower()
            song_valence, song_arousal = self.MOOD_VA_MAP.get(song_mood, (0.0, 0.0))
        
        # Get target VA (from context or derived from mood)
        target_valence = context.target_valence
        target_arousal = context.target_arousal
        
        if target_valence == 0.0 and target_arousal == 0.0:
            target_valence, target_arousal = self.MOOD_VA_MAP.get(
                context.target_mood.lower(), (0.0, 0.0)
            )
        
        # Compute Euclidean distance
        distance = math.sqrt(
            (song_valence - target_valence) ** 2 +
            (song_arousal - target_arousal) ** 2
        )
        
        # Normalize to [0, 1] where 1 = perfect match
        score = 1.0 - (distance / self.MAX_DISTANCE)
        score = max(0.0, min(1.0, score))
        
        # Confidence based on how well-defined the song's VA coordinates are
        confidence = 0.9 if (song_valence != 0.0 or song_arousal != 0.0) else 0.6
        
        return StrategyScore(
            strategy=self.strategy_type,
            score=score,
            confidence=confidence,
            components={
                'va_distance': distance,
                'song_valence': song_valence,
                'song_arousal': song_arousal,
                'target_valence': target_valence,
                'target_arousal': target_arousal,
            },
            explanation=self._generate_explanation(score, song, context)
        )
    
    def _generate_explanation(
        self,
        score: float,
        song: Dict[str, Any],
        context: RecommendationContext
    ) -> str:
        """Generate explanation for emotion matching."""
        if score >= 0.8:
            return f"closely matches your {context.target_mood} mood"
        elif score >= 0.6:
            return f"has a similar emotional tone to {context.target_mood}"
        elif score >= 0.4:
            return f"offers a gentle transition from {context.target_mood}"
        else:
            return f"provides emotional contrast to {context.target_mood}"
    
    def explain(
        self,
        song: Dict[str, Any],
        score: StrategyScore,
        context: RecommendationContext
    ) -> str:
        return score.explanation


# =============================================================================
# CONTENT SIMILARITY STRATEGY
# =============================================================================

class ContentStrategy(RecommendationStrategy):
    """
    Content-based similarity using audio features and metadata.
    
    Features:
    - Genre matching
    - Artist similarity
    - Tempo similarity
    - Audio feature cosine similarity
    """
    
    strategy_type = StrategyType.CONTENT
    
    GENRE_SIMILARITY = {
        ('pop', 'dance'): 0.7,
        ('rock', 'metal'): 0.7,
        ('hip-hop', 'r&b'): 0.7,
        ('jazz', 'blues'): 0.8,
        ('classical', 'instrumental'): 0.7,
        ('electronic', 'dance'): 0.8,
        ('indie', 'alternative'): 0.8,
    }
    
    def score(
        self,
        song: Dict[str, Any],
        context: RecommendationContext
    ) -> StrategyScore:
        """Score based on content similarity to user preferences."""
        
        components = {}
        
        # Genre similarity
        song_genre = song.get('genre', '').lower()
        preferred_genres = context.user_preferences.get('genres', {})
        
        genre_score = 0.0
        if preferred_genres:
            genre_score = preferred_genres.get(song_genre, 0.0)
            # Check for similar genres
            for pref_genre, pref_weight in preferred_genres.items():
                sim = self._genre_similarity(song_genre, pref_genre)
                genre_score = max(genre_score, pref_weight * sim)
        else:
            genre_score = 0.5  # Neutral if no preferences
        
        components['genre_score'] = genre_score
        
        # Artist similarity
        song_artist = song.get('artist', '').lower()
        preferred_artists = context.user_preferences.get('artists', {})
        artist_score = preferred_artists.get(song_artist, 0.3)
        components['artist_score'] = artist_score
        
        # Tempo similarity (if target tempo known)
        song_tempo = song.get('tempo', 120)
        target_tempo = context.explicit_constraints.get('tempo', 120)
        tempo_score = 1.0 - min(abs(song_tempo - target_tempo) / 60, 1.0)
        components['tempo_score'] = tempo_score
        
        # Audio features (energy, danceability, acousticness)
        feature_scores = []
        for feature in ['energy', 'danceability', 'acousticness']:
            song_val = song.get(feature, 0.5)
            target_val = context.explicit_constraints.get(feature, 0.5)
            feature_scores.append(1.0 - abs(song_val - target_val))
        
        audio_score = sum(feature_scores) / len(feature_scores) if feature_scores else 0.5
        components['audio_features_score'] = audio_score
        
        # Weighted combination
        final_score = (
            0.35 * genre_score +
            0.25 * artist_score +
            0.15 * tempo_score +
            0.25 * audio_score
        )
        
        return StrategyScore(
            strategy=self.strategy_type,
            score=final_score,
            confidence=0.85,
            components=components,
            explanation=self._generate_explanation(components, song)
        )
    
    def _genre_similarity(self, genre1: str, genre2: str) -> float:
        """Get similarity between two genres."""
        if genre1 == genre2:
            return 1.0
        
        key = tuple(sorted([genre1, genre2]))
        return self.GENRE_SIMILARITY.get(key, 0.3)
    
    def _generate_explanation(
        self,
        components: Dict[str, float],
        song: Dict[str, Any]
    ) -> str:
        """Generate content-based explanation."""
        reasons = []
        
        if components.get('genre_score', 0) > 0.6:
            reasons.append(f"in the {song.get('genre', 'similar')} genre you enjoy")
        
        if components.get('artist_score', 0) > 0.5:
            reasons.append(f"by {song.get('artist', 'an artist')} you've liked")
        
        if components.get('audio_features_score', 0) > 0.7:
            reasons.append("with audio qualities matching your taste")
        
        if reasons:
            return " and ".join(reasons)
        return "matches your listening profile"
    
    def explain(
        self,
        song: Dict[str, Any],
        score: StrategyScore,
        context: RecommendationContext
    ) -> str:
        return score.explanation


# =============================================================================
# COLLABORATIVE FILTERING STRATEGY
# =============================================================================

class CollaborativeStrategy(RecommendationStrategy):
    """
    Collaborative filtering based on similar users' preferences.
    
    Uses item-based collaborative filtering with implicit feedback.
    """
    
    strategy_type = StrategyType.COLLABORATIVE
    
    def __init__(self, user_similarity_fn: Callable = None):
        """
        Initialize with optional user similarity function.
        
        Args:
            user_similarity_fn: Function(user_id, song_id) -> score
        """
        self.user_similarity_fn = user_similarity_fn
    
    def score(
        self,
        song: Dict[str, Any],
        context: RecommendationContext
    ) -> StrategyScore:
        """Score based on collaborative signals."""
        
        song_id = song.get('song_id', song.get('id', 0))
        
        # Use external similarity function if provided
        if self.user_similarity_fn:
            collab_score = self.user_similarity_fn(context.user_id, song_id)
        else:
            # Fallback to popularity-based scoring
            play_count = song.get('play_count', 0)
            like_count = song.get('like_count', 0)
            
            # Normalize with log scaling
            popularity = math.log1p(play_count) / math.log1p(10000)
            like_ratio = like_count / max(play_count, 1)
            
            collab_score = 0.6 * min(popularity, 1.0) + 0.4 * like_ratio
        
        return StrategyScore(
            strategy=self.strategy_type,
            score=min(1.0, collab_score),
            confidence=0.7,
            components={
                'collaborative_score': collab_score,
                'play_count': song.get('play_count', 0),
                'like_count': song.get('like_count', 0),
            },
            explanation=self._generate_explanation(collab_score, song)
        )
    
    def _generate_explanation(self, score: float, song: Dict) -> str:
        """Generate collaborative explanation."""
        if score > 0.7:
            return "loved by listeners with similar taste"
        elif score > 0.5:
            return "popular among users like you"
        else:
            return "discovered by the community"
    
    def explain(
        self,
        song: Dict[str, Any],
        score: StrategyScore,
        context: RecommendationContext
    ) -> str:
        return score.explanation


# =============================================================================
# DIVERSITY STRATEGY
# =============================================================================

class DiversityStrategy(RecommendationStrategy):
    """
    Diversity injection to prevent filter bubbles.
    
    Ensures variety in:
    - Artists
    - Genres
    - Tempo ranges
    - Release years
    """
    
    strategy_type = StrategyType.DIVERSITY
    
    def __init__(self, config: StrategyConfig = None):
        self.config = config or StrategyConfig()
    
    def score(
        self,
        song: Dict[str, Any],
        context: RecommendationContext
    ) -> StrategyScore:
        """Score based on diversity from recent recommendations."""
        
        session_songs = context.session_songs
        user_history = context.user_history[-self.config.diversity_window_size:]
        
        if not session_songs and not user_history:
            # No history = maximum diversity score
            return StrategyScore(
                strategy=self.strategy_type,
                score=1.0,
                confidence=1.0,
                components={'diversity_type': 'no_history'},
                explanation="offers a fresh listening experience"
            )
        
        diversity_penalties = []
        
        # Artist diversity
        song_artist = song.get('artist', '').lower()
        recent_artists = [
            h.get('artist', '').lower() 
            for h in user_history if h.get('artist')
        ]
        artist_penalty = recent_artists.count(song_artist) * 0.3
        diversity_penalties.append(min(artist_penalty, 1.0))
        
        # Genre diversity
        song_genre = song.get('genre', '').lower()
        recent_genres = [
            h.get('genre', '').lower()
            for h in user_history if h.get('genre')
        ]
        genre_penalty = recent_genres.count(song_genre) * 0.15
        diversity_penalties.append(min(genre_penalty, 1.0))
        
        # Session song diversity (higher penalty for songs in current session)
        song_id = song.get('song_id', song.get('id', 0))
        if song_id in context.session_songs:
            diversity_penalties.append(1.0)  # Already in session
        
        # Calculate diversity score (inverse of penalty)
        avg_penalty = sum(diversity_penalties) / len(diversity_penalties)
        diversity_score = max(self.config.min_diversity_score, 1.0 - avg_penalty)
        
        return StrategyScore(
            strategy=self.strategy_type,
            score=diversity_score,
            confidence=0.9,
            components={
                'artist_penalty': diversity_penalties[0] if diversity_penalties else 0,
                'genre_penalty': diversity_penalties[1] if len(diversity_penalties) > 1 else 0,
                'average_penalty': avg_penalty,
            },
            explanation=self._generate_explanation(diversity_score, song)
        )
    
    def _generate_explanation(self, score: float, song: Dict) -> str:
        """Generate diversity explanation."""
        if score > 0.8:
            return "brings something new to your session"
        elif score > 0.5:
            return "adds variety to your playlist"
        else:
            return "familiar but still enjoyable"
    
    def explain(
        self,
        song: Dict[str, Any],
        score: StrategyScore,
        context: RecommendationContext
    ) -> str:
        return score.explanation


# =============================================================================
# EXPLORATION STRATEGY
# =============================================================================

class ExplorationStrategy(RecommendationStrategy):
    """
    Exploration component for discovering new content.
    
    Promotes songs that:
    - User hasn't heard before
    - Are outside user's typical preferences
    - Have low exposure in the system
    """
    
    strategy_type = StrategyType.EXPLORATION
    
    def score(
        self,
        song: Dict[str, Any],
        context: RecommendationContext
    ) -> StrategyScore:
        """Score based on exploration potential."""
        
        components = {}
        
        # Novelty: has user heard this before?
        song_id = song.get('song_id', song.get('id', 0))
        heard_songs = {h.get('song_id') for h in context.user_history}
        novelty_score = 0.0 if song_id in heard_songs else 1.0
        components['novelty'] = novelty_score
        
        # Discovery: is this outside user's typical preferences?
        preferred_genres = set(context.user_preferences.get('genres', {}).keys())
        song_genre = song.get('genre', '').lower()
        discovery_score = 0.8 if song_genre not in preferred_genres else 0.3
        components['discovery'] = discovery_score
        
        # Low exposure in system (hidden gems)
        play_count = song.get('play_count', 0)
        exposure_score = 1.0 - min(math.log1p(play_count) / math.log1p(1000), 1.0)
        components['low_exposure'] = exposure_score
        
        # Random boost for true exploration
        random_boost = random.random() * 0.2
        components['random_boost'] = random_boost
        
        # Weighted combination
        exploration_score = (
            0.4 * novelty_score +
            0.25 * discovery_score +
            0.25 * exposure_score +
            0.1 * random_boost
        )
        
        return StrategyScore(
            strategy=self.strategy_type,
            score=exploration_score,
            confidence=0.6,  # Lower confidence for exploration
            components=components,
            explanation=self._generate_explanation(components, song)
        )
    
    def _generate_explanation(self, components: Dict, song: Dict) -> str:
        """Generate exploration explanation."""
        if components.get('novelty', 0) > 0.5:
            return "a new discovery for you"
        elif components.get('discovery', 0) > 0.5:
            return "outside your usual style"
        elif components.get('low_exposure', 0) > 0.5:
            return "a hidden gem worth exploring"
        else:
            return "something different to try"
    
    def explain(
        self,
        song: Dict[str, Any],
        score: StrategyScore,
        context: RecommendationContext
    ) -> str:
        return score.explanation


# =============================================================================
# EXPLORATION/EXPLOITATION BALANCER
# =============================================================================

class ExplorationExploitationBalancer:
    """
    Balances exploration and exploitation using various methods.
    
    Implements:
    - ε-greedy
    - UCB1 (Upper Confidence Bound)
    - Thompson Sampling
    - Softmax (Boltzmann)
    """
    
    def __init__(self, config: StrategyConfig = None):
        self.config = config or StrategyConfig()
        self.strategy_performance: Dict[StrategyType, StrategyPerformance] = {
            st: StrategyPerformance(strategy=st) for st in StrategyType
        }
    
    def select_weights(
        self,
        method: ExplorationMethod,
        context: RecommendationContext
    ) -> Dict[StrategyType, float]:
        """
        Select strategy weights using specified method.
        
        Args:
            method: Exploration method to use
            context: Recommendation context
            
        Returns:
            Dictionary of strategy weights
        """
        if method == ExplorationMethod.EPSILON_GREEDY:
            return self._epsilon_greedy()
        elif method == ExplorationMethod.UCB1:
            return self._ucb1()
        elif method == ExplorationMethod.THOMPSON_SAMPLING:
            return self._thompson_sampling()
        elif method == ExplorationMethod.SOFTMAX:
            return self._softmax()
        else:
            return self._default_weights()
    
    def _epsilon_greedy(self) -> Dict[StrategyType, float]:
        """ε-greedy strategy selection."""
        weights = {}
        
        if random.random() < self.config.exploration_rate:
            # Explore: equal weights
            for st in StrategyType:
                weights[st] = 1.0 / len(StrategyType)
        else:
            # Exploit: weight by performance
            total_reward = sum(
                perf.average_reward 
                for perf in self.strategy_performance.values()
            )
            
            for st in StrategyType:
                if total_reward > 0:
                    weights[st] = self.strategy_performance[st].average_reward / total_reward
                else:
                    weights[st] = 1.0 / len(StrategyType)
        
        return self._normalize_weights(weights)
    
    def _ucb1(self) -> Dict[StrategyType, float]:
        """UCB1 (Upper Confidence Bound) strategy selection."""
        weights = {}
        total_pulls = sum(perf.total_pulls for perf in self.strategy_performance.values())
        
        for st in StrategyType:
            perf = self.strategy_performance[st]
            
            if perf.total_pulls == 0:
                # Encourage trying untried strategies
                ucb_value = float('inf')
            else:
                # UCB1 formula: avg_reward + c * sqrt(ln(t) / n_i)
                exploitation = perf.average_reward
                exploration = self.config.ucb_confidence * math.sqrt(
                    math.log(max(total_pulls, 1)) / perf.total_pulls
                )
                ucb_value = exploitation + exploration
            
            weights[st] = ucb_value
        
        return self._normalize_weights(weights)
    
    def _thompson_sampling(self) -> Dict[StrategyType, float]:
        """Thompson Sampling using Beta distribution."""
        weights = {}
        
        for st in StrategyType:
            perf = self.strategy_performance[st]
            
            # Beta distribution parameters
            alpha = self.config.thompson_alpha + perf.successes
            beta = self.config.thompson_beta + perf.failures
            
            # Sample from Beta distribution
            sampled_value = random.betavariate(alpha, beta)
            weights[st] = sampled_value
        
        return self._normalize_weights(weights)
    
    def _softmax(self, temperature: float = 1.0) -> Dict[StrategyType, float]:
        """Softmax (Boltzmann) exploration."""
        weights = {}
        
        # Get average rewards
        rewards = {
            st: self.strategy_performance[st].average_reward
            for st in StrategyType
        }
        
        # Softmax with temperature
        max_reward = max(rewards.values()) if rewards else 0
        exp_sum = sum(
            math.exp((r - max_reward) / temperature)
            for r in rewards.values()
        )
        
        for st, reward in rewards.items():
            weights[st] = math.exp((reward - max_reward) / temperature) / exp_sum
        
        return weights
    
    def _default_weights(self) -> Dict[StrategyType, float]:
        """Default strategy weights from config."""
        return {
            StrategyType.EMOTION: self.config.emotion_weight,
            StrategyType.CONTENT: self.config.content_weight,
            StrategyType.COLLABORATIVE: self.config.collaborative_weight,
            StrategyType.DIVERSITY: self.config.diversity_weight,
            StrategyType.EXPLORATION: self.config.exploration_weight,
        }
    
    def _normalize_weights(self, weights: Dict[StrategyType, float]) -> Dict[StrategyType, float]:
        """Normalize weights to sum to 1.0."""
        total = sum(weights.values())
        if total > 0:
            return {k: v / total for k, v in weights.items()}
        return self._default_weights()
    
    def update_performance(
        self,
        strategy: StrategyType,
        reward: float,
        success: bool
    ):
        """Update performance tracking after feedback."""
        perf = self.strategy_performance[strategy]
        perf.total_pulls += 1
        perf.cumulative_reward += reward
        
        if success:
            perf.successes += 1
        else:
            perf.failures += 1
        
        perf.last_updated = datetime.now()


# =============================================================================
# MULTI-STRATEGY ENGINE
# =============================================================================

class MultiStrategyEngine:
    """
    Multi-strategy recommendation engine with adaptive weight selection.
    
    Combines multiple strategies using exploration/exploitation balancing
    to generate diverse, personalized recommendations.
    
    Usage:
        engine = MultiStrategyEngine()
        
        context = RecommendationContext(
            user_id=user_id,
            target_mood="happy",
            user_preferences=user_prefs,
        )
        
        result = engine.recommend(
            candidates=song_list,
            context=context,
            top_k=10,
        )
    """
    
    def __init__(
        self,
        config: StrategyConfig = None,
        exploration_method: ExplorationMethod = ExplorationMethod.THOMPSON_SAMPLING
    ):
        self.config = config or StrategyConfig()
        self.config.validate()
        
        self.exploration_method = exploration_method
        self.balancer = ExplorationExploitationBalancer(self.config)
        
        # Initialize strategies
        self.strategies: Dict[StrategyType, RecommendationStrategy] = {
            StrategyType.EMOTION: EmotionStrategy(),
            StrategyType.CONTENT: ContentStrategy(),
            StrategyType.COLLABORATIVE: CollaborativeStrategy(),
            StrategyType.DIVERSITY: DiversityStrategy(self.config),
            StrategyType.EXPLORATION: ExplorationStrategy(),
        }
    
    def recommend(
        self,
        candidates: List[Dict[str, Any]],
        context: RecommendationContext,
        top_k: int = 10,
        explain: bool = True
    ) -> RecommendationResult:
        """
        Generate recommendations using multi-strategy approach.
        
        Args:
            candidates: List of candidate songs
            context: Recommendation context
            top_k: Number of recommendations to return
            explain: Whether to generate explanations
            
        Returns:
            RecommendationResult with ranked songs
        """
        # Get dynamic strategy weights
        strategy_weights = self.balancer.select_weights(
            self.exploration_method, context
        )
        
        # Apply context modifiers
        context_modifiers = self._compute_context_modifiers(context)
        strategy_weights = self._apply_context_modifiers(
            strategy_weights, context_modifiers
        )
        
        # Score all candidates
        scored_candidates = []
        
        for song in candidates:
            candidate = CandidateSong(
                song_id=song.get('song_id', song.get('id', 0)),
                song_data=song
            )
            
            # Score with each strategy
            weighted_score = 0.0
            weighted_confidence = 0.0
            
            for strategy_type, strategy in self.strategies.items():
                score = strategy.score(song, context)
                candidate.strategy_scores[strategy_type] = score
                
                weight = strategy_weights.get(strategy_type, 0.0)
                weighted_score += weight * score.score
                weighted_confidence += weight * score.confidence
            
            candidate.final_score = weighted_score
            candidate.final_confidence = weighted_confidence
            
            # Determine dominant strategy for explanation
            if candidate.strategy_scores:
                dominant = max(
                    candidate.strategy_scores.items(),
                    key=lambda x: x[1].score * strategy_weights.get(x[0], 0.0)
                )
                candidate.selected_strategy = dominant[0]
            
            # Generate explanation
            if explain:
                candidate.explanation_components = self._generate_explanation(
                    candidate, context, strategy_weights
                )
            
            scored_candidates.append(candidate)
        
        # Sort by score and select top_k
        scored_candidates.sort(key=lambda c: c.final_score, reverse=True)
        top_candidates = scored_candidates[:top_k]
        
        return RecommendationResult(
            songs=top_candidates,
            strategy_weights_used=strategy_weights,
            exploration_method=self.exploration_method,
            context_modifiers=context_modifiers,
            metadata={
                'total_candidates': len(candidates),
                'top_k': top_k,
                'timestamp': datetime.now().isoformat(),
            }
        )
    
    def _compute_context_modifiers(
        self,
        context: RecommendationContext
    ) -> Dict[str, float]:
        """Compute context-based weight modifiers."""
        modifiers = {}
        
        if self.config.time_of_day_modifier and context.time_of_day:
            # Adjust for time of day
            time_mods = {
                'morning': {'energy': 0.8, 'calm': 1.2},
                'afternoon': {'energy': 1.0, 'exploration': 1.1},
                'evening': {'calm': 1.1, 'romantic': 1.2},
                'night': {'calm': 1.3, 'melancholy': 1.1},
            }
            modifiers['time_of_day'] = time_mods.get(context.time_of_day, {})
        
        if self.config.session_length_modifier:
            # Increase diversity as session progresses
            turn_factor = min(context.session_turn / 10, 1.0)
            modifiers['session_diversity_boost'] = 1.0 + (0.3 * turn_factor)
        
        if self.config.mood_intensity_modifier:
            # Adjust emotion weight based on intensity
            modifiers['emotion_intensity'] = 0.8 + (0.4 * context.target_intensity)
        
        return modifiers
    
    def _apply_context_modifiers(
        self,
        weights: Dict[StrategyType, float],
        modifiers: Dict[str, Any]
    ) -> Dict[StrategyType, float]:
        """Apply context modifiers to strategy weights."""
        modified = weights.copy()
        
        # Apply session diversity boost
        if 'session_diversity_boost' in modifiers:
            boost = modifiers['session_diversity_boost']
            modified[StrategyType.DIVERSITY] *= boost
        
        # Apply emotion intensity modifier
        if 'emotion_intensity' in modifiers:
            modified[StrategyType.EMOTION] *= modifiers['emotion_intensity']
        
        # Re-normalize
        total = sum(modified.values())
        if total > 0:
            return {k: v / total for k, v in modified.items()}
        return weights
    
    def _generate_explanation(
        self,
        candidate: CandidateSong,
        context: RecommendationContext,
        weights: Dict[StrategyType, float]
    ) -> List[str]:
        """Generate natural language explanation components."""
        explanations = []
        
        # Get top contributing strategies
        contributions = [
            (st, score.score * weights.get(st, 0.0), score.explanation)
            for st, score in candidate.strategy_scores.items()
            if score.score > 0.3
        ]
        contributions.sort(key=lambda x: x[1], reverse=True)
        
        # Take top 2-3 explanations
        for strategy_type, _, explanation in contributions[:3]:
            if explanation:
                explanations.append(explanation)
        
        return explanations
    
    def process_feedback(
        self,
        song_id: int,
        feedback_type: str,
        selected_strategy: StrategyType = None
    ):
        """
        Process user feedback to update strategy performance.
        
        Args:
            song_id: ID of the song
            feedback_type: 'like', 'dislike', 'skip'
            selected_strategy: Strategy that was dominant for this recommendation
        """
        reward_map = {
            'like': 1.0,
            'play': 0.5,
            'complete': 0.7,
            'skip': -0.3,
            'dislike': -1.0,
        }
        
        reward = reward_map.get(feedback_type, 0.0)
        success = feedback_type in ('like', 'play', 'complete')
        
        if selected_strategy:
            self.balancer.update_performance(selected_strategy, reward, success)
        else:
            # Distribute reward across all strategies
            for st in StrategyType:
                self.balancer.update_performance(st, reward / len(StrategyType), success)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_multi_strategy_engine(
    config: StrategyConfig = None,
    exploration_method: str = "thompson"
) -> MultiStrategyEngine:
    """Create a MultiStrategyEngine instance."""
    method_map = {
        "epsilon": ExplorationMethod.EPSILON_GREEDY,
        "ucb": ExplorationMethod.UCB1,
        "thompson": ExplorationMethod.THOMPSON_SAMPLING,
        "softmax": ExplorationMethod.SOFTMAX,
    }
    
    method = method_map.get(exploration_method.lower(), ExplorationMethod.THOMPSON_SAMPLING)
    return MultiStrategyEngine(config, method)
