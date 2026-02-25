"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - EMOTION DEPTH TRACKER
=============================================================================

Tracks emotional depth across conversation turns, accumulating signals
and building a comprehensive understanding of the user's emotional state.

The EmotionDepthTracker is responsible for:
1. Accumulating emotional signals from multiple turns
2. Tracking mood history and detecting consistency
3. Managing the EmotionalContext lifecycle
4. Computing aggregate emotional metrics (valence, arousal)

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import json

from .types import (
    EmotionalContext,
    EmotionalSignals,
    ContextSignals,
    MoodHistoryEntry,
    ConversationTurn,
    MoodCategory,
    IntensityLevel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Mood to VA (Valence-Arousal) space mapping
# Valence: -1.0 (negative) to 1.0 (positive)
# Arousal: 0.0 (calm) to 1.0 (excited)
MOOD_VA_MAPPING: Dict[str, Tuple[float, float]] = {
    "Vui": (0.8, 0.7),           # Happy: high valence, high arousal
    "Buồn": (-0.7, 0.3),         # Sad: low valence, low arousal
    "Suy tư": (0.0, 0.3),        # Thoughtful: neutral valence, low arousal
    "Chill": (0.3, 0.2),         # Relaxed: slightly positive, low arousal
    "Năng lượng": (0.6, 0.9),    # Energetic: positive valence, high arousal
    "Tập trung": (0.2, 0.5),     # Focused: slightly positive, medium arousal
    # English mappings
    "happy": (0.8, 0.7),
    "sad": (-0.7, 0.3),
    "thoughtful": (0.0, 0.3),
    "chill": (0.3, 0.2),
    "relaxed": (0.3, 0.2),
    "energetic": (0.6, 0.9),
    "focused": (0.2, 0.5),
}

# Intensity multipliers for arousal
INTENSITY_AROUSAL_MULTIPLIER: Dict[str, float] = {
    "Nhẹ": 0.6,
    "Vừa": 1.0,
    "Mạnh": 1.3,
    "light": 0.6,
    "medium": 1.0,
    "strong": 1.3,
}

# Decay factor for older mood observations
MOOD_HISTORY_DECAY = 0.9  # Each turn back reduces weight by 10%

# Minimum confidence to consider a mood observation valid
MIN_MOOD_CONFIDENCE = 0.3


# =============================================================================
# EMOTION DEPTH TRACKER
# =============================================================================

class EmotionDepthTracker:
    """
    Tracks emotional depth and accumulates signals across conversation turns.
    
    The tracker maintains:
    - Mood history with weighted confidence
    - VA space estimates
    - Context accumulation
    - Consistency scoring
    
    Usage:
        tracker = EmotionDepthTracker()
        context = tracker.create_context()
        
        # Process each turn
        tracker.process_turn(context, turn)
        
        # Get current understanding
        mood, confidence = tracker.get_primary_mood(context)
    """
    
    def __init__(self):
        self._mood_va_map = MOOD_VA_MAPPING.copy()
        self._intensity_multipliers = INTENSITY_AROUSAL_MULTIPLIER.copy()
    
    def create_context(self) -> EmotionalContext:
        """
        Create a new EmotionalContext for a session.
        
        Returns:
            Fresh EmotionalContext instance
        """
        return EmotionalContext(
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    
    def process_turn(self, context: EmotionalContext,
                     turn: ConversationTurn) -> EmotionalContext:
        """
        Process a conversation turn and update emotional context.
        
        This is the main entry point for updating context based on turn data.
        
        Args:
            context: Current emotional context
            turn: Conversation turn with detected signals
            
        Returns:
            Updated EmotionalContext
        """
        # Extract signals from turn
        emotional_signals = turn.emotional_signals or self._extract_signals_from_turn(turn)
        context_signals = turn.context_signals or ContextSignals()
        
        # Update mood tracking
        if emotional_signals.mood and emotional_signals.confidence >= MIN_MOOD_CONFIDENCE:
            self._update_mood_tracking(context, emotional_signals, turn.turn_number)
        
        # Update intensity
        if emotional_signals.intensity:
            self._update_intensity(context, emotional_signals)
        
        # Update VA estimates
        self._update_va_estimates(context)
        
        # Merge context signals
        if context_signals:
            context.merge_context(context_signals)
        
        # Update keywords
        if emotional_signals.keywords_matched:
            context.all_keywords.extend(emotional_signals.keywords_matched)
            context.all_keywords = list(set(context.all_keywords))
        
        # Track clarification attempts
        context.clarification_attempts = turn.turn_number + 1
        
        # Update timestamp
        context.updated_at = datetime.now()
        
        return context
    
    def _extract_signals_from_turn(self, turn: ConversationTurn) -> EmotionalSignals:
        """
        Extract EmotionalSignals from turn data if not already present.
        """
        return EmotionalSignals(
            mood=turn.detected_mood,
            confidence=turn.mood_confidence,
            intensity=turn.detected_intensity,
            keywords_matched=turn.keywords_matched or [],
        )
    
    def _update_mood_tracking(self, context: EmotionalContext,
                              signals: EmotionalSignals,
                              turn_number: int):
        """
        Update mood tracking with new observation.
        
        Uses weighted history where more recent observations have higher weight.
        """
        # Add to history
        entry = MoodHistoryEntry(
            mood=signals.mood,
            confidence=signals.confidence,
            turn_number=turn_number,
            source='explicit' if signals.is_explicit else 'nlp',
        )
        context.mood_history.append(entry)
        
        # Compute weighted primary mood
        mood_scores: Dict[str, float] = {}
        
        for i, hist_entry in enumerate(context.mood_history):
            # Apply decay based on recency
            recency = len(context.mood_history) - 1 - i
            weight = (MOOD_HISTORY_DECAY ** recency) * hist_entry.confidence
            
            if hist_entry.mood not in mood_scores:
                mood_scores[hist_entry.mood] = 0.0
            mood_scores[hist_entry.mood] += weight
        
        # Find highest scoring mood
        if mood_scores:
            best_mood = max(mood_scores, key=mood_scores.get)
            best_score = mood_scores[best_mood]
            
            # Normalize score
            total = sum(mood_scores.values())
            normalized_confidence = best_score / total if total > 0 else 0.0
            
            # Update primary mood
            context.primary_mood = best_mood
            context.mood_confidence = min(1.0, normalized_confidence)
            context.mood_specified = True
        
        # Update consistency
        self._update_consistency(context)
    
    def _update_intensity(self, context: EmotionalContext, signals: EmotionalSignals):
        """
        Update intensity tracking.
        """
        if signals.intensity:
            context.primary_intensity = signals.intensity
            context.intensity_specified = True
    
    def _update_va_estimates(self, context: EmotionalContext):
        """
        Update Valence-Arousal space estimates based on current mood.
        """
        if not context.primary_mood:
            return
        
        # Get base VA from mood
        va = self._mood_va_map.get(context.primary_mood)
        if not va:
            # Try lowercase
            va = self._mood_va_map.get(context.primary_mood.lower())
        
        if va:
            base_valence, base_arousal = va
            
            # Apply intensity modifier to arousal
            intensity = context.primary_intensity or "Vừa"
            arousal_mult = self._intensity_multipliers.get(intensity, 1.0)
            
            context.valence_estimate = base_valence
            context.arousal_estimate = min(1.0, base_arousal * arousal_mult)
    
    def _update_consistency(self, context: EmotionalContext):
        """
        Update mood consistency score based on history.
        
        Consistency measures how stable the detected mood has been.
        Oscillating between moods = low consistency.
        """
        if len(context.mood_history) < 2:
            context.consistency_score = 1.0
            return
        
        # Count unique moods and transitions
        unique_moods = set(e.mood for e in context.mood_history)
        transitions = 0
        
        for i in range(1, len(context.mood_history)):
            if context.mood_history[i].mood != context.mood_history[i-1].mood:
                transitions += 1
        
        # Consistency formula:
        # - Fewer unique moods = higher consistency
        # - Fewer transitions = higher consistency
        unique_penalty = max(0, len(unique_moods) - 1) * 0.2
        transition_penalty = transitions * 0.15
        
        context.consistency_score = max(0.0, 1.0 - unique_penalty - transition_penalty)
    
    def get_primary_mood(self, context: EmotionalContext) -> Tuple[Optional[str], float]:
        """
        Get the current primary mood and confidence.
        
        Returns:
            Tuple of (mood_string, confidence)
        """
        return context.primary_mood, context.mood_confidence
    
    def get_va_coordinates(self, context: EmotionalContext) -> Tuple[float, float]:
        """
        Get current VA space coordinates.
        
        Returns:
            Tuple of (valence, arousal)
        """
        return context.valence_estimate, context.arousal_estimate
    
    def needs_more_probing(self, context: EmotionalContext,
                           clarity_threshold: float = 0.6) -> bool:
        """
        Determine if more probing is needed.
        
        Args:
            context: Current emotional context
            clarity_threshold: Minimum clarity to stop probing
            
        Returns:
            True if more probing recommended
        """
        # Need mood
        if not context.primary_mood or context.mood_confidence < clarity_threshold:
            return True
        
        # Need intensity for precise recommendations
        if not context.intensity_specified:
            return True
        
        # Low consistency might need clarification
        if context.consistency_score < 0.5 and len(context.mood_history) >= 2:
            return True
        
        return False
    
    def get_mood_summary(self, context: EmotionalContext) -> Dict[str, Any]:
        """
        Get a summary of the current mood understanding.
        
        Returns:
            Dict with mood, intensity, confidence, and metadata
        """
        return {
            'primary_mood': context.primary_mood,
            'primary_intensity': context.primary_intensity,
            'confidence': context.mood_confidence,
            'consistency': context.consistency_score,
            'valence': context.valence_estimate,
            'arousal': context.arousal_estimate,
            'specified': {
                'mood': context.mood_specified,
                'intensity': context.intensity_specified,
            },
            'history_length': len(context.mood_history),
            'keywords': context.all_keywords[:10],  # Top 10
        }
    
    def reset(self, context: EmotionalContext):
        """
        Reset emotional tracking for mood correction.
        
        This clears mood history while preserving context signals.
        """
        context.primary_mood = None
        context.primary_intensity = None
        context.mood_confidence = 0.0
        context.mood_history.clear()
        context.mood_specified = False
        context.intensity_specified = False
        context.consistency_score = 1.0
        context.valence_estimate = 0.0
        context.arousal_estimate = 0.5
        context.requires_clarification = True
        # Keep: context signals, keywords, clarification_attempts
        context.updated_at = datetime.now()
    
    def apply_correction(self, context: EmotionalContext,
                         correct_mood: str,
                         correct_intensity: Optional[str] = None):
        """
        Apply a user mood correction.
        
        This updates the primary mood with high confidence (user explicitly corrected).
        
        Args:
            context: Current emotional context
            correct_mood: The corrected mood
            correct_intensity: Optional corrected intensity
        """
        # Add correction to history with high confidence
        entry = MoodHistoryEntry(
            mood=correct_mood,
            confidence=1.0,  # User correction = 100% confidence
            turn_number=len(context.mood_history),
            source='correction',
        )
        context.mood_history.append(entry)
        
        # Update primary mood
        context.primary_mood = correct_mood
        context.mood_confidence = 0.95  # High but not 1.0 to allow further refinement
        context.mood_specified = True
        
        # Update intensity if provided
        if correct_intensity:
            context.primary_intensity = correct_intensity
            context.intensity_specified = True
        
        # Update VA
        self._update_va_estimates(context)
        
        # Mark as clarified
        context.requires_clarification = False
        context.updated_at = datetime.now()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_emotion_tracker() -> EmotionDepthTracker:
    """
    Create an EmotionDepthTracker instance.
    """
    return EmotionDepthTracker()


def mood_to_va(mood: str, intensity: Optional[str] = None) -> Tuple[float, float]:
    """
    Convert mood (and optional intensity) to VA coordinates.
    
    Args:
        mood: Mood string (Vietnamese or English)
        intensity: Optional intensity level
        
    Returns:
        Tuple of (valence, arousal)
    """
    va = MOOD_VA_MAPPING.get(mood) or MOOD_VA_MAPPING.get(mood.lower(), (0.0, 0.5))
    valence, arousal = va
    
    if intensity:
        mult = INTENSITY_AROUSAL_MULTIPLIER.get(intensity, 1.0)
        arousal = min(1.0, arousal * mult)
    
    return valence, arousal
