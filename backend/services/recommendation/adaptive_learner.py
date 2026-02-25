"""
=============================================================================
ADAPTIVE LEARNING SYSTEM
=============================================================================

Dynamic weight adjustment based on user feedback and listening behavior.

Learning Formula:
================

    new_weight = old_weight + α * feedback_signal * decay_factor

Where:
    α (alpha) = learning rate, typically 0.1
    feedback_signal:
        - like: +1.0
        - skip: -0.5
        - dislike: -1.0
    decay_factor = exp(-λ * days_since_last_interaction)

Weight Bounds:
=============

To prevent weight explosion:
    w_min = 0.1
    w_max = 3.0

Decay over time ensures unused preferences fade:
    weight_t = weight_0 * exp(-λ * t)

Where λ is the decay rate (default: 0.01 per day)

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
class LearningConfig:
    """Configuration for adaptive learning."""
    
    # Learning rates (α)
    alpha_like: float = 0.15       # Learning rate for likes
    alpha_skip: float = 0.08       # Learning rate for skips
    alpha_dislike: float = 0.12    # Learning rate for dislikes
    
    # Feedback signals
    signal_like: float = 1.0       # Signal for like
    signal_skip: float = -0.5      # Signal for skip
    signal_dislike: float = -1.0   # Signal for dislike
    
    # Weight bounds
    weight_min: float = 0.1        # Minimum weight
    weight_max: float = 3.0        # Maximum weight
    weight_default: float = 1.0    # Default/neutral weight
    
    # Time decay
    decay_lambda: float = 0.01     # Decay rate per day
    decay_half_life_days: int = 69 # ln(2)/0.01 ≈ 69 days
    
    # Batch update settings
    batch_window_hours: int = 24   # Batch updates within this window
    min_interactions: int = 3      # Min interactions before updating
    
    # Confidence settings
    confidence_boost_per_interaction: float = 0.05
    confidence_max: float = 0.95


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class FeedbackType(Enum):
    """Types of user feedback."""
    LIKE = 'like'
    SKIP = 'skip'
    DISLIKE = 'dislike'
    PLAY_COMPLETE = 'play_complete'  # Listened > 80%
    PLAY_PARTIAL = 'play_partial'    # Listened 30-80%
    PLAY_MINIMAL = 'play_minimal'    # Listened < 30%


@dataclass
class FeedbackSignal:
    """
    A single feedback signal from user interaction.
    """
    user_id: int
    song_id: int
    feedback_type: FeedbackType
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Optional metadata
    listened_duration_seconds: Optional[int] = None
    song_duration_seconds: Optional[int] = None
    mood_context: Optional[str] = None
    session_id: Optional[str] = None
    
    # Song attributes for learning
    song_mood: Optional[str] = None
    song_genre: Optional[str] = None
    song_artist: Optional[str] = None
    
    def get_signal_value(self, config: LearningConfig = None) -> float:
        """Get numeric signal value."""
        config = config or LearningConfig()
        
        signal_map = {
            FeedbackType.LIKE: config.signal_like,
            FeedbackType.DISLIKE: config.signal_dislike,
            FeedbackType.SKIP: config.signal_skip,
            FeedbackType.PLAY_COMPLETE: config.signal_like * 0.8,
            FeedbackType.PLAY_PARTIAL: 0.0,  # Neutral
            FeedbackType.PLAY_MINIMAL: config.signal_skip * 0.5,
        }
        
        return signal_map.get(self.feedback_type, 0.0)
    
    def get_learning_rate(self, config: LearningConfig = None) -> float:
        """Get learning rate for this feedback type."""
        config = config or LearningConfig()
        
        rate_map = {
            FeedbackType.LIKE: config.alpha_like,
            FeedbackType.DISLIKE: config.alpha_dislike,
            FeedbackType.SKIP: config.alpha_skip,
            FeedbackType.PLAY_COMPLETE: config.alpha_like * 0.7,
            FeedbackType.PLAY_PARTIAL: config.alpha_skip * 0.3,
            FeedbackType.PLAY_MINIMAL: config.alpha_skip * 0.5,
        }
        
        return rate_map.get(self.feedback_type, config.alpha_skip)


@dataclass
class WeightUpdate:
    """
    Record of a weight update.
    """
    user_id: int
    category: str  # 'mood', 'genre', 'artist'
    item: str      # Specific mood/genre/artist
    old_weight: float
    new_weight: float
    delta: float
    feedback_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'category': self.category,
            'item': self.item,
            'old_weight': round(self.old_weight, 4),
            'new_weight': round(self.new_weight, 4),
            'delta': round(self.delta, 4),
            'feedback_count': self.feedback_count,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class UserPreferences:
    """
    User preference weights.
    """
    user_id: int
    mood_weights: Dict[str, float] = field(default_factory=dict)
    genre_weights: Dict[str, float] = field(default_factory=dict)
    artist_weights: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0
    confidence: float = 0.5
    
    def get_weight(self, category: str, item: str, default: float = 1.0) -> float:
        """Get weight for a specific item."""
        weights = getattr(self, f'{category}_weights', {})
        return weights.get(item, default)
    
    def set_weight(self, category: str, item: str, weight: float):
        """Set weight for a specific item."""
        weights = getattr(self, f'{category}_weights', {})
        weights[item] = weight
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage/API."""
        return {
            'mood': self.mood_weights,
            'genre': self.genre_weights,
            'artist': self.artist_weights,
            'last_updated': self.last_updated.isoformat(),
            'interaction_count': self.interaction_count,
            'confidence': self.confidence,
        }
    
    @classmethod
    def from_dict(cls, user_id: int, data: Dict) -> 'UserPreferences':
        """Create from dict."""
        prefs = cls(user_id=user_id)
        prefs.mood_weights = data.get('mood', {})
        prefs.genre_weights = data.get('genre', {})
        prefs.artist_weights = data.get('artist', {})
        
        if 'last_updated' in data:
            try:
                prefs.last_updated = datetime.fromisoformat(data['last_updated'])
            except:
                pass
        
        prefs.interaction_count = data.get('interaction_count', 0)
        prefs.confidence = data.get('confidence', 0.5)
        
        return prefs


# =============================================================================
# ADAPTIVE LEARNER
# =============================================================================

class AdaptiveLearner:
    """
    Adaptive learning system for user preferences.
    
    Implements:
    - Incremental weight updates from feedback
    - Time-based weight decay
    - Weight bounds enforcement
    - Batch update processing
    - Confidence tracking
    
    Usage:
        learner = AdaptiveLearner()
        
        # Process single feedback
        updates = learner.process_feedback(signal, current_prefs)
        
        # Process batch of feedback
        updates = learner.process_batch(signals, current_prefs)
        
        # Apply decay to stale preferences
        decayed_prefs = learner.apply_decay(prefs, days_elapsed)
    """
    
    def __init__(self, config: LearningConfig = None):
        """
        Initialize learner.
        
        Args:
            config: Learning configuration
        """
        self.config = config or LearningConfig()
    
    # =========================================================================
    # MAIN LEARNING METHODS
    # =========================================================================
    
    def process_feedback(
        self,
        signal: FeedbackSignal,
        current_prefs: UserPreferences
    ) -> List[WeightUpdate]:
        """
        Process a single feedback signal and update preferences.
        
        Algorithm:
            new_weight = clamp(old_weight + α * signal, w_min, w_max)
        
        Args:
            signal: Feedback signal
            current_prefs: Current user preferences
            
        Returns:
            List of weight updates applied
        """
        updates = []
        
        signal_value = signal.get_signal_value(self.config)
        learning_rate = signal.get_learning_rate(self.config)
        
        # Update mood weight
        if signal.song_mood:
            update = self._update_weight(
                current_prefs,
                category='mood',
                item=signal.song_mood,
                signal_value=signal_value,
                learning_rate=learning_rate
            )
            if update:
                updates.append(update)
        
        # Update genre weight
        if signal.song_genre:
            update = self._update_weight(
                current_prefs,
                category='genre',
                item=signal.song_genre,
                signal_value=signal_value,
                learning_rate=learning_rate
            )
            if update:
                updates.append(update)
        
        # Update artist weight
        if signal.song_artist:
            update = self._update_weight(
                current_prefs,
                category='artist',
                item=signal.song_artist,
                signal_value=signal_value,
                learning_rate=learning_rate * 0.5  # Lower rate for artist
            )
            if update:
                updates.append(update)
        
        # Update metadata
        current_prefs.interaction_count += 1
        current_prefs.confidence = min(
            self.config.confidence_max,
            current_prefs.confidence + self.config.confidence_boost_per_interaction
        )
        
        return updates
    
    def process_batch(
        self,
        signals: List[FeedbackSignal],
        current_prefs: UserPreferences
    ) -> List[WeightUpdate]:
        """
        Process a batch of feedback signals.
        
        Batching improves stability by averaging signals before updating.
        
        Args:
            signals: List of feedback signals
            current_prefs: Current user preferences
            
        Returns:
            List of weight updates
        """
        if not signals:
            return []
        
        # Group signals by (category, item)
        aggregated: Dict[Tuple[str, str], List[Tuple[float, float]]] = {}
        
        for signal in signals:
            signal_value = signal.get_signal_value(self.config)
            learning_rate = signal.get_learning_rate(self.config)
            
            if signal.song_mood:
                key = ('mood', signal.song_mood)
                if key not in aggregated:
                    aggregated[key] = []
                aggregated[key].append((signal_value, learning_rate))
            
            if signal.song_genre:
                key = ('genre', signal.song_genre)
                if key not in aggregated:
                    aggregated[key] = []
                aggregated[key].append((signal_value, learning_rate))
            
            if signal.song_artist:
                key = ('artist', signal.song_artist)
                if key not in aggregated:
                    aggregated[key] = []
                aggregated[key].append((signal_value, learning_rate * 0.5))
        
        # Apply aggregated updates
        updates = []
        
        for (category, item), values in aggregated.items():
            # Average signal and learning rate
            avg_signal = sum(v[0] for v in values) / len(values)
            avg_rate = sum(v[1] for v in values) / len(values)
            
            update = self._update_weight(
                current_prefs,
                category=category,
                item=item,
                signal_value=avg_signal,
                learning_rate=avg_rate
            )
            if update:
                update.feedback_count = len(values)
                updates.append(update)
        
        # Update metadata
        current_prefs.interaction_count += len(signals)
        current_prefs.confidence = min(
            self.config.confidence_max,
            current_prefs.confidence + self.config.confidence_boost_per_interaction * len(signals)
        )
        
        return updates
    
    def _update_weight(
        self,
        prefs: UserPreferences,
        category: str,
        item: str,
        signal_value: float,
        learning_rate: float
    ) -> Optional[WeightUpdate]:
        """
        Update a single weight.
        
        Formula:
            new_weight = clamp(old_weight + α * signal, w_min, w_max)
        """
        old_weight = prefs.get_weight(category, item, self.config.weight_default)
        
        # Calculate delta
        delta = learning_rate * signal_value
        
        # Calculate new weight with bounds
        new_weight = old_weight + delta
        new_weight = max(self.config.weight_min, min(self.config.weight_max, new_weight))
        
        # Skip if no significant change
        if abs(new_weight - old_weight) < 0.001:
            return None
        
        # Apply update
        prefs.set_weight(category, item, new_weight)
        
        return WeightUpdate(
            user_id=prefs.user_id,
            category=category,
            item=item,
            old_weight=old_weight,
            new_weight=new_weight,
            delta=new_weight - old_weight,
            feedback_count=1
        )
    
    # =========================================================================
    # DECAY METHODS
    # =========================================================================
    
    def apply_decay(
        self,
        prefs: UserPreferences,
        days_elapsed: float = None
    ) -> UserPreferences:
        """
        Apply time-based decay to all weights.
        
        Formula:
            weight_t = weight_default + (weight_0 - weight_default) * exp(-λ * t)
        
        This decays weights toward the default value, not toward zero.
        
        Args:
            prefs: User preferences to decay
            days_elapsed: Days since last update (computed if None)
            
        Returns:
            Updated preferences
        """
        if days_elapsed is None:
            days_elapsed = (datetime.now() - prefs.last_updated).total_seconds() / 86400
        
        if days_elapsed < 1:
            return prefs  # No decay for recent preferences
        
        decay_factor = math.exp(-self.config.decay_lambda * days_elapsed)
        default = self.config.weight_default
        
        # Decay mood weights
        for item, weight in prefs.mood_weights.items():
            decayed = default + (weight - default) * decay_factor
            prefs.mood_weights[item] = decayed
        
        # Decay genre weights
        for item, weight in prefs.genre_weights.items():
            decayed = default + (weight - default) * decay_factor
            prefs.genre_weights[item] = decayed
        
        # Decay artist weights
        for item, weight in prefs.artist_weights.items():
            decayed = default + (weight - default) * decay_factor
            prefs.artist_weights[item] = decayed
        
        # Decay confidence
        prefs.confidence *= decay_factor
        prefs.confidence = max(0.3, prefs.confidence)  # Minimum confidence
        
        return prefs
    
    def compute_decay_factor(self, days: float) -> float:
        """
        Compute decay factor for given number of days.
        
        Formula:
            decay_factor = exp(-λ * days)
        """
        return math.exp(-self.config.decay_lambda * days)
    
    # =========================================================================
    # ANALYSIS METHODS
    # =========================================================================
    
    def compute_preference_strength(
        self,
        prefs: UserPreferences,
        category: str
    ) -> Dict[str, float]:
        """
        Compute normalized preference strengths.
        
        Returns weights normalized so that:
        - Neutral (1.0) → 0.5
        - Min (0.1) → 0.0
        - Max (3.0) → 1.0
        """
        weights = getattr(prefs, f'{category}_weights', {})
        
        result = {}
        for item, weight in weights.items():
            # Normalize from [0.1, 3.0] to [0.0, 1.0]
            normalized = (weight - self.config.weight_min) / (self.config.weight_max - self.config.weight_min)
            result[item] = max(0.0, min(1.0, normalized))
        
        return result
    
    def get_top_preferences(
        self,
        prefs: UserPreferences,
        category: str,
        k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get top k preferences in a category.
        """
        weights = getattr(prefs, f'{category}_weights', {})
        
        sorted_items = sorted(
            weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_items[:k]
    
    def get_preference_summary(
        self,
        prefs: UserPreferences
    ) -> Dict[str, Any]:
        """
        Get summary of user preferences.
        """
        return {
            'top_moods': self.get_top_preferences(prefs, 'mood', 3),
            'top_genres': self.get_top_preferences(prefs, 'genre', 3),
            'top_artists': self.get_top_preferences(prefs, 'artist', 3),
            'interaction_count': prefs.interaction_count,
            'confidence': prefs.confidence,
            'last_updated': prefs.last_updated.isoformat(),
            'days_since_update': (datetime.now() - prefs.last_updated).days,
        }
    
    # =========================================================================
    # FEEDBACK SIGNAL CREATION
    # =========================================================================
    
    @staticmethod
    def create_signal_from_feedback(
        user_id: int,
        song_id: int,
        feedback_type: str,
        song_data: Dict[str, Any] = None,
        **kwargs
    ) -> FeedbackSignal:
        """
        Create a FeedbackSignal from raw feedback data.
        
        Args:
            user_id: User ID
            song_id: Song ID
            feedback_type: 'like', 'dislike', 'skip', etc.
            song_data: Optional song metadata
            **kwargs: Additional signal attributes
            
        Returns:
            FeedbackSignal instance
        """
        # Map string to enum
        type_map = {
            'like': FeedbackType.LIKE,
            'dislike': FeedbackType.DISLIKE,
            'skip': FeedbackType.SKIP,
            'complete': FeedbackType.PLAY_COMPLETE,
            'partial': FeedbackType.PLAY_PARTIAL,
            'minimal': FeedbackType.PLAY_MINIMAL,
        }
        
        fb_type = type_map.get(feedback_type.lower(), FeedbackType.SKIP)
        
        # Extract song attributes if provided
        song_mood = None
        song_genre = None
        song_artist = None
        
        if song_data:
            song_mood = song_data.get('mood')
            song_genre = song_data.get('genre')
            song_artist = song_data.get('artist')
        
        return FeedbackSignal(
            user_id=user_id,
            song_id=song_id,
            feedback_type=fb_type,
            song_mood=song_mood,
            song_genre=song_genre,
            song_artist=song_artist,
            **kwargs
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_adaptive_learner(config: LearningConfig = None) -> AdaptiveLearner:
    """Create an AdaptiveLearner instance."""
    return AdaptiveLearner(config)
