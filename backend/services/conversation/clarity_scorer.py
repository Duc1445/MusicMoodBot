"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - EMOTION CLARITY MODEL
=============================================================================

Computes a clarity score indicating how well we understand the user's
emotional state based on multiple weighted components.

The clarity score determines:
- Whether to continue probing
- Whether to proceed to recommendations
- Confidence level for recommendations

Clarity Formula:
  clarity = Σ(weight[i] × component_score[i])

Components:
  1. mood_score: Is a specific mood detected?
  2. intensity_score: Is intensity level known?
  3. confidence_score: How confident is the mood detection?
  4. context_score: How much context do we have?
  5. consistency_score: How consistent has the mood been?

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, Any

from .types import (
    EmotionalContext,
    CLARITY_THRESHOLD_HIGH,
    CLARITY_THRESHOLD_MEDIUM,
    CLARITY_THRESHOLD_LOW,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ClarityWeights:
    """
    Weights for each clarity component.
    
    Weights should sum to 1.0 for normalized scoring.
    """
    mood_specified: float = 0.35      # Did user specify a mood?
    mood_confidence: float = 0.25     # How confident is detection?
    intensity_specified: float = 0.15 # Did user specify intensity?
    context_richness: float = 0.10    # How much context do we have?
    consistency: float = 0.15         # How consistent is the mood?
    
    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = (
            self.mood_specified +
            self.mood_confidence +
            self.intensity_specified +
            self.context_richness +
            self.consistency
        )
        if abs(total - 1.0) > 0.001:
            logger.warning(f"Clarity weights sum to {total}, expected 1.0")
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'mood_specified': self.mood_specified,
            'mood_confidence': self.mood_confidence,
            'intensity_specified': self.intensity_specified,
            'context_richness': self.context_richness,
            'consistency': self.consistency,
        }


# Default weights
DEFAULT_WEIGHTS = ClarityWeights()

# Alternative weight profiles for different scenarios
WEIGHT_PROFILES = {
    # Quick recommendations - prioritize having any mood
    'quick': ClarityWeights(
        mood_specified=0.50,
        mood_confidence=0.20,
        intensity_specified=0.10,
        context_richness=0.05,
        consistency=0.15,
    ),
    # Detailed recommendations - want full context
    'detailed': ClarityWeights(
        mood_specified=0.25,
        mood_confidence=0.25,
        intensity_specified=0.20,
        context_richness=0.15,
        consistency=0.15,
    ),
    # Balanced (default)
    'balanced': DEFAULT_WEIGHTS,
}


# =============================================================================
# CLARITY COMPONENTS
# =============================================================================

@dataclass
class ClarityComponents:
    """
    Individual clarity component scores (0.0 - 1.0 each).
    """
    mood_specified: float = 0.0
    mood_confidence: float = 0.0
    intensity_specified: float = 0.0
    context_richness: float = 0.0
    consistency: float = 1.0  # Default high (no contradictions yet)
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'mood_specified': self.mood_specified,
            'mood_confidence': self.mood_confidence,
            'intensity_specified': self.intensity_specified,
            'context_richness': self.context_richness,
            'consistency': self.consistency,
        }


@dataclass
class ClarityResult:
    """
    Result of clarity scoring.
    """
    score: float                      # Overall clarity (0.0 - 1.0)
    components: ClarityComponents     # Individual component scores
    weights: ClarityWeights           # Weights used
    level: str                        # 'high', 'medium', 'low', 'insufficient'
    can_recommend: bool               # Ready to recommend?
    needs_probing: bool               # Should probe more?
    probing_priority: str             # 'mood', 'intensity', 'context', 'none'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'score': self.score,
            'components': self.components.to_dict(),
            'weights': self.weights.to_dict(),
            'level': self.level,
            'can_recommend': self.can_recommend,
            'needs_probing': self.needs_probing,
            'probing_priority': self.probing_priority,
        }


# =============================================================================
# EMOTION CLARITY MODEL
# =============================================================================

class EmotionClarityModel:
    """
    Computes clarity score for emotional understanding.
    
    The clarity score is a weighted sum of component scores,
    each measuring a different aspect of our understanding.
    
    Formula:
        clarity = Σ(weight[i] × component[i])
    
    Where:
        - mood_specified: 1.0 if mood is known, 0.0 otherwise
        - mood_confidence: The NLP confidence score
        - intensity_specified: 1.0 if intensity is known, 0.0 otherwise
        - context_richness: How much context (time, activity, etc.)
        - consistency: How stable the mood detection has been
    
    Usage:
        model = EmotionClarityModel()
        result = model.compute(emotional_context)
        
        if result.can_recommend:
            # Proceed to recommendations
        else:
            # Probe for more info
            what_to_probe = result.probing_priority
    """
    
    def __init__(self, weights: Optional[ClarityWeights] = None,
                 profile: str = 'balanced'):
        """
        Initialize clarity model.
        
        Args:
            weights: Custom weights, or None to use profile
            profile: Weight profile name ('quick', 'detailed', 'balanced')
        """
        if weights:
            self.weights = weights
        else:
            self.weights = WEIGHT_PROFILES.get(profile, DEFAULT_WEIGHTS)
    
    def compute(self, context: EmotionalContext) -> ClarityResult:
        """
        Compute clarity score for the given emotional context.
        
        Args:
            context: EmotionalContext with accumulated signals
            
        Returns:
            ClarityResult with score and analysis
        """
        # Compute individual component scores
        components = self._compute_components(context)
        
        # Compute weighted sum
        score = self._compute_weighted_sum(components)
        
        # Determine level
        level = self._determine_level(score)
        
        # Determine if ready to recommend
        can_recommend = self._can_recommend(score, components, context)
        
        # Determine probing priority
        needs_probing = not can_recommend
        probing_priority = self._determine_probing_priority(components) if needs_probing else 'none'
        
        return ClarityResult(
            score=score,
            components=components,
            weights=self.weights,
            level=level,
            can_recommend=can_recommend,
            needs_probing=needs_probing,
            probing_priority=probing_priority,
        )
    
    def _compute_components(self, context: EmotionalContext) -> ClarityComponents:
        """
        Compute individual clarity component scores.
        """
        return ClarityComponents(
            mood_specified=1.0 if context.mood_specified else 0.0,
            mood_confidence=context.mood_confidence,
            intensity_specified=1.0 if context.intensity_specified else 0.0,
            context_richness=context.context_richness,
            consistency=context.consistency_score,
        )
    
    def _compute_weighted_sum(self, components: ClarityComponents) -> float:
        """
        Compute weighted sum of components.
        """
        score = (
            self.weights.mood_specified * components.mood_specified +
            self.weights.mood_confidence * components.mood_confidence +
            self.weights.intensity_specified * components.intensity_specified +
            self.weights.context_richness * components.context_richness +
            self.weights.consistency * components.consistency
        )
        return min(1.0, max(0.0, score))  # Clamp to [0, 1]
    
    def _determine_level(self, score: float) -> str:
        """
        Determine clarity level from score.
        """
        if score >= CLARITY_THRESHOLD_HIGH:
            return 'high'
        elif score >= CLARITY_THRESHOLD_MEDIUM:
            return 'medium'
        elif score >= CLARITY_THRESHOLD_LOW:
            return 'low'
        else:
            return 'insufficient'
    
    def _can_recommend(self, score: float, components: ClarityComponents,
                       context: EmotionalContext) -> bool:
        """
        Determine if we have enough clarity to recommend.
        
        Requirements:
        - Must have a mood (mood_specified = 1.0)
        - Score must be at least MEDIUM or context is exhausted
        """
        # Must have mood
        if components.mood_specified < 1.0:
            return False
        
        # High clarity = definitely recommend
        if score >= CLARITY_THRESHOLD_HIGH:
            return True
        
        # Medium clarity with decent confidence
        if score >= CLARITY_THRESHOLD_MEDIUM and components.mood_confidence >= 0.5:
            return True
        
        # Max clarification attempts reached
        if context.clarification_attempts >= 3:
            return True
        
        return False
    
    def _determine_probing_priority(self, components: ClarityComponents) -> str:
        """
        Determine what to probe for next based on component gaps.
        
        Priority order:
        1. Mood (if not specified)
        2. Intensity (if mood known but intensity not)
        3. Context (if both are known but context thin)
        """
        # Mood is highest priority
        if components.mood_specified < 1.0:
            return 'mood'
        
        # Then intensity
        if components.intensity_specified < 1.0 and components.mood_confidence >= 0.5:
            return 'intensity'
        
        # Then context
        if components.context_richness < 0.3:
            return 'context'
        
        # Low consistency might need mood clarification
        if components.consistency < 0.5:
            return 'mood'  # Re-probe mood to clarify
        
        return 'none'
    
    def compute_delta(self, before: ClarityResult, after: ClarityResult) -> float:
        """
        Compute change in clarity between two results.
        
        Args:
            before: Clarity before turn
            after: Clarity after turn
            
        Returns:
            Delta (positive = improvement)
        """
        return after.score - before.score
    
    def set_profile(self, profile: str):
        """
        Switch to a different weight profile.
        
        Args:
            profile: Profile name ('quick', 'detailed', 'balanced')
        """
        if profile in WEIGHT_PROFILES:
            self.weights = WEIGHT_PROFILES[profile]
        else:
            logger.warning(f"Unknown profile '{profile}', using balanced")
            self.weights = DEFAULT_WEIGHTS
    
    def set_custom_weights(self, weights: ClarityWeights):
        """
        Set custom weights.
        
        Args:
            weights: Custom ClarityWeights instance
        """
        self.weights = weights


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_clarity_model(profile: str = 'balanced') -> EmotionClarityModel:
    """
    Create an EmotionClarityModel with given profile.
    
    Args:
        profile: 'quick', 'detailed', or 'balanced'
        
    Returns:
        Configured EmotionClarityModel
    """
    return EmotionClarityModel(profile=profile)


def compute_quick_clarity(context: EmotionalContext) -> float:
    """
    Quick clarity computation without full result object.
    
    Args:
        context: EmotionalContext
        
    Returns:
        Clarity score (0.0 - 1.0)
    """
    model = EmotionClarityModel()
    result = model.compute(context)
    return result.score


def clarity_level_from_score(score: float) -> str:
    """
    Get clarity level name from score.
    
    Args:
        score: Clarity score (0.0 - 1.0)
        
    Returns:
        Level name ('high', 'medium', 'low', 'insufficient')
    """
    if score >= CLARITY_THRESHOLD_HIGH:
        return 'high'
    elif score >= CLARITY_THRESHOLD_MEDIUM:
        return 'medium'
    elif score >= CLARITY_THRESHOLD_LOW:
        return 'low'
    else:
        return 'insufficient'
