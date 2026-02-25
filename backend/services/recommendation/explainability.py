"""
=============================================================================
EXPLAINABLE RECOMMENDATION MODULE
=============================================================================

Generates natural language explanations for recommendations by referencing
extracted emotional signals and contributing factors.

Features:
=========
1. Template-based explanation generation
2. Dynamic factor highlighting
3. Emotional signal referencing
4. Personalized explanation style
5. Multi-language support (placeholder)

Explanation Structure:
=====================
"This song is recommended because [PRIMARY_REASON].
 It [EMOTIONAL_MATCH] and [SECONDARY_REASONS].
 [CONFIDENCE_INDICATOR]"

Author: MusicMoodBot Team
Version: 4.0.0
=============================================================================
"""

from __future__ import annotations

import random
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class ExplanationStyle(Enum):
    """Styles for explanation generation."""
    CASUAL = "casual"          # Friendly, conversational
    DETAILED = "detailed"      # Technical, comprehensive
    MINIMAL = "minimal"        # Brief, essential info only
    EMOTIONAL = "emotional"    # Focus on emotional aspects


@dataclass
class ExplanationConfig:
    """Configuration for explanation generation."""
    style: ExplanationStyle = ExplanationStyle.CASUAL
    max_reasons: int = 3
    include_confidence: bool = True
    include_emotional_signal: bool = True
    include_strategy_breakdown: bool = False
    emoji_enabled: bool = False


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class EmotionalSignal:
    """Extracted emotional signal from conversation."""
    detected_mood: str
    confidence: float
    valence: float
    arousal: float
    intensity: float
    keywords: List[str] = field(default_factory=list)
    context_phrases: List[str] = field(default_factory=list)


@dataclass
class ExplanationFactor:
    """A single factor contributing to the recommendation."""
    factor_type: str  # emotion, content, collaborative, diversity, exploration
    weight: float     # How much this factor contributed
    score: float      # Score for this factor
    description: str  # Human-readable description
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecommendationExplanation:
    """Complete explanation for a recommendation."""
    song_id: int
    song_name: str
    artist: str
    
    # Primary explanation
    headline: str
    full_explanation: str
    
    # Emotional connection
    emotional_match: str
    detected_signals: List[str]
    
    # Contributing factors
    factors: List[ExplanationFactor]
    
    # Confidence
    overall_confidence: float
    confidence_statement: str
    
    # Metadata
    style: ExplanationStyle = ExplanationStyle.CASUAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'song_id': self.song_id,
            'song_name': self.song_name,
            'artist': self.artist,
            'headline': self.headline,
            'full_explanation': self.full_explanation,
            'emotional_match': self.emotional_match,
            'detected_signals': self.detected_signals,
            'factors': [
                {
                    'type': f.factor_type,
                    'weight': round(f.weight, 2),
                    'score': round(f.score, 2),
                    'description': f.description,
                }
                for f in self.factors
            ],
            'confidence': round(self.overall_confidence, 2),
            'confidence_statement': self.confidence_statement,
        }


# =============================================================================
# EXPLANATION TEMPLATES
# =============================================================================

class ExplanationTemplates:
    """Template library for generating explanations."""
    
    # Casual style templates
    CASUAL_HEADLINES = {
        'high_emotion': [
            "Perfect match for your {mood} mood!",
            "This one really fits your vibe",
            "Exactly what you're looking for",
        ],
        'medium_emotion': [
            "Great choice for {mood} vibes",
            "Should fit your mood nicely",
            "A solid pick for how you're feeling",
        ],
        'low_emotion': [
            "Something a bit different",
            "Worth giving a try",
            "A fresh perspective",
        ],
    }
    
    EMOTION_MATCHES = {
        'happy': [
            "has uplifting energy that matches your happy mood",
            "brings positive vibes aligned with how you're feeling",
            "radiates the same joyful energy you expressed",
        ],
        'sad': [
            "resonates with those melancholic feelings",
            "understands the sadness you're experiencing",
            "embraces the emotional depth you're feeling",
        ],
        'calm': [
            "has the peaceful quality you're seeking",
            "offers the tranquility you need right now",
            "creates a serene atmosphere matching your state",
        ],
        'excited': [
            "matches your high energy and enthusiasm",
            "has the same electric excitement you're feeling",
            "brings the intensity your mood craves",
        ],
        'angry': [
            "channels that intense emotion constructively",
            "acknowledges the fire in your mood",
            "has the raw energy matching your feelings",
        ],
        'anxious': [
            "helps process those nervous feelings",
            "can help soothe anxiety",
            "acknowledges your emotional state",
        ],
        'romantic': [
            "captures that romantic feeling perfectly",
            "has the warmth and intimacy you're seeking",
            "sets the perfect romantic mood",
        ],
        'nostalgic': [
            "evokes similar nostalgic feelings",
            "takes you back in time",
            "connects with those bittersweet memories",
        ],
        'default': [
            "connects with your emotional state",
            "resonates with how you're feeling",
            "matches your current mood",
        ],
    }
    
    FACTOR_DESCRIPTIONS = {
        'emotion': [
            "emotionally aligned with your mood",
            "has the right emotional energy",
            "matches your emotional wavelength",
        ],
        'content': [
            "fits your taste in {genre} music",
            "by {artist}, an artist you enjoy",
            "has the musical qualities you prefer",
        ],
        'collaborative': [
            "loved by listeners with similar taste",
            "popular among users like you",
            "recommended by the community",
        ],
        'diversity': [
            "adds variety to your listening",
            "brings something fresh",
            "expands your musical horizons",
        ],
        'exploration': [
            "a new discovery for you",
            "worth exploring",
            "outside your usual picks",
        ],
    }
    
    CONFIDENCE_STATEMENTS = {
        'high': [
            "I'm very confident you'll enjoy this",
            "This is a strong match for you",
            "Highly recommended based on your preferences",
        ],
        'medium': [
            "I think you'll like this one",
            "Good match for what you're looking for",
            "Should suit your current mood",
        ],
        'low': [
            "This might surprise you in a good way",
            "Worth a try if you're open to something new",
            "Could be an interesting discovery",
        ],
    }
    
    # Detailed style templates
    DETAILED_TEMPLATE = """
**Recommendation Analysis for "{song_name}" by {artist}**

**Primary Match Factor:** {primary_factor}

**Emotional Analysis:**
- Detected mood: {detected_mood} (confidence: {mood_confidence:.0%})
- Song emotional profile: Valence {valence:.2f}, Arousal {arousal:.2f}
- Match score: {emotion_score:.0%}

**Contributing Factors:**
{factor_breakdown}

**Overall Confidence:** {overall_confidence:.0%}
{confidence_reasoning}
"""
    
    # Minimal style template
    MINIMAL_TEMPLATE = "{headline}. {primary_reason}."
    
    @classmethod
    def get_headline(
        cls,
        style: ExplanationStyle,
        emotion_score: float,
        mood: str
    ) -> str:
        """Get appropriate headline based on style and score."""
        if style == ExplanationStyle.MINIMAL:
            if emotion_score >= 0.7:
                return "Great match"
            elif emotion_score >= 0.4:
                return "Good fit"
            else:
                return "Worth trying"
        
        # Casual and Emotional styles
        if emotion_score >= 0.7:
            templates = cls.CASUAL_HEADLINES['high_emotion']
        elif emotion_score >= 0.4:
            templates = cls.CASUAL_HEADLINES['medium_emotion']
        else:
            templates = cls.CASUAL_HEADLINES['low_emotion']
        
        return random.choice(templates).format(mood=mood)
    
    @classmethod
    def get_emotion_match(cls, mood: str) -> str:
        """Get emotional match description."""
        mood_key = mood.lower()
        templates = cls.EMOTION_MATCHES.get(mood_key, cls.EMOTION_MATCHES['default'])
        return random.choice(templates)
    
    @classmethod
    def get_factor_description(
        cls,
        factor_type: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Get factor description."""
        templates = cls.FACTOR_DESCRIPTIONS.get(factor_type, ['relevant to your taste'])
        description = random.choice(templates)
        
        if context:
            description = description.format(**context)
        
        return description
    
    @classmethod
    def get_confidence_statement(cls, confidence: float) -> str:
        """Get confidence statement."""
        if confidence >= 0.7:
            return random.choice(cls.CONFIDENCE_STATEMENTS['high'])
        elif confidence >= 0.4:
            return random.choice(cls.CONFIDENCE_STATEMENTS['medium'])
        else:
            return random.choice(cls.CONFIDENCE_STATEMENTS['low'])


# =============================================================================
# EXPLANATION GENERATOR
# =============================================================================

class ExplainableRecommendation:
    """
    Generates natural language explanations for recommendations.
    
    Takes scoring components and emotional signals to create
    human-readable explanations that reference detected emotions.
    
    Usage:
        explainer = ExplainableRecommendation(config)
        
        explanation = explainer.explain(
            song=song_data,
            scores=strategy_scores,
            emotional_signal=detected_emotion,
            context=user_context,
        )
        
        print(explanation.full_explanation)
    """
    
    def __init__(self, config: ExplanationConfig = None):
        self.config = config or ExplanationConfig()
        self.templates = ExplanationTemplates()
    
    def explain(
        self,
        song: Dict[str, Any],
        scores: Dict[str, float],
        strategy_contributions: Dict[str, float] = None,
        emotional_signal: EmotionalSignal = None,
        context: Dict[str, Any] = None
    ) -> RecommendationExplanation:
        """
        Generate explanation for a recommendation.
        
        Args:
            song: Song data dictionary
            scores: Scores from different strategies
            strategy_contributions: Weighted contributions of each strategy
            emotional_signal: Detected emotional signal from user
            context: Additional context (user preferences, etc.)
            
        Returns:
            RecommendationExplanation object
        """
        context = context or {}
        strategy_contributions = strategy_contributions or {}
        
        # Extract emotional signal or create default
        if emotional_signal is None:
            emotional_signal = EmotionalSignal(
                detected_mood=context.get('mood', 'neutral'),
                confidence=context.get('confidence', 0.5),
                valence=context.get('valence', 0.0),
                arousal=context.get('arousal', 0.0),
                intensity=context.get('intensity', 0.5),
            )
        
        # Build explanation factors
        factors = self._build_factors(scores, strategy_contributions, song, context)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_confidence(scores, factors)
        
        # Get emotion score for headline selection
        emotion_score = scores.get('emotion', scores.get('mood_similarity', 0.5))
        
        # Generate components based on style
        headline = self.templates.get_headline(
            self.config.style,
            emotion_score,
            emotional_signal.detected_mood
        )
        
        emotional_match = self._generate_emotional_match(
            song, emotional_signal
        )
        
        detected_signals = self._format_detected_signals(emotional_signal)
        
        confidence_statement = self.templates.get_confidence_statement(overall_confidence)
        
        # Generate full explanation
        full_explanation = self._generate_full_explanation(
            song,
            headline,
            emotional_match,
            factors,
            confidence_statement,
            emotional_signal
        )
        
        return RecommendationExplanation(
            song_id=song.get('song_id', song.get('id', 0)),
            song_name=song.get('song_name', song.get('name', 'Unknown')),
            artist=song.get('artist', 'Unknown Artist'),
            headline=headline,
            full_explanation=full_explanation,
            emotional_match=emotional_match,
            detected_signals=detected_signals,
            factors=factors,
            overall_confidence=overall_confidence,
            confidence_statement=confidence_statement,
            style=self.config.style,
        )
    
    def _build_factors(
        self,
        scores: Dict[str, float],
        contributions: Dict[str, float],
        song: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[ExplanationFactor]:
        """Build explanation factors from scores."""
        factors = []
        
        # Map score keys to factor types
        score_to_type = {
            'emotion': 'emotion',
            'mood_similarity': 'emotion',
            'content': 'content',
            'content_similarity': 'content',
            'collaborative': 'collaborative',
            'diversity': 'diversity',
            'exploration': 'exploration',
        }
        
        for score_key, score_value in scores.items():
            if score_value <= 0:
                continue
            
            factor_type = score_to_type.get(score_key)
            if not factor_type:
                continue
            
            weight = contributions.get(score_key, 0.2)
            
            # Build context for description
            desc_context = {
                'genre': song.get('genre', 'music'),
                'artist': song.get('artist', 'this artist'),
            }
            
            description = self.templates.get_factor_description(
                factor_type, desc_context
            )
            
            factors.append(ExplanationFactor(
                factor_type=factor_type,
                weight=weight,
                score=score_value,
                description=description,
                evidence={'score_key': score_key, 'raw_score': score_value},
            ))
        
        # Sort by weighted contribution
        factors.sort(key=lambda f: f.weight * f.score, reverse=True)
        
        # Limit to max_reasons
        return factors[:self.config.max_reasons]
    
    def _calculate_confidence(
        self,
        scores: Dict[str, float],
        factors: List[ExplanationFactor]
    ) -> float:
        """Calculate overall explanation confidence."""
        if not scores:
            return 0.5
        
        # Weighted average of factor scores
        total_weight = sum(f.weight for f in factors)
        if total_weight > 0:
            weighted_score = sum(f.weight * f.score for f in factors) / total_weight
        else:
            weighted_score = sum(scores.values()) / len(scores)
        
        return min(1.0, weighted_score)
    
    def _generate_emotional_match(
        self,
        song: Dict[str, Any],
        signal: EmotionalSignal
    ) -> str:
        """Generate emotional match description."""
        mood = signal.detected_mood
        return self.templates.get_emotion_match(mood)
    
    def _format_detected_signals(
        self,
        signal: EmotionalSignal
    ) -> List[str]:
        """Format detected emotional signals for display."""
        signals = []
        
        signals.append(f"Detected mood: {signal.detected_mood}")
        
        if signal.keywords:
            signals.append(f"Keywords: {', '.join(signal.keywords[:3])}")
        
        if signal.intensity != 0.5:
            intensity_label = "high" if signal.intensity > 0.7 else "low" if signal.intensity < 0.3 else "moderate"
            signals.append(f"Intensity: {intensity_label}")
        
        return signals
    
    def _generate_full_explanation(
        self,
        song: Dict[str, Any],
        headline: str,
        emotional_match: str,
        factors: List[ExplanationFactor],
        confidence_statement: str,
        signal: EmotionalSignal
    ) -> str:
        """Generate complete explanation text."""
        
        if self.config.style == ExplanationStyle.DETAILED:
            return self._generate_detailed_explanation(
                song, headline, emotional_match, factors,
                confidence_statement, signal
            )
        
        elif self.config.style == ExplanationStyle.MINIMAL:
            primary = factors[0].description if factors else "matches your taste"
            return f"{headline}. It {primary}."
        
        elif self.config.style == ExplanationStyle.EMOTIONAL:
            return self._generate_emotional_explanation(
                song, headline, emotional_match, signal
            )
        
        else:  # CASUAL (default)
            return self._generate_casual_explanation(
                song, headline, emotional_match, factors,
                confidence_statement
            )
    
    def _generate_casual_explanation(
        self,
        song: Dict[str, Any],
        headline: str,
        emotional_match: str,
        factors: List[ExplanationFactor],
        confidence_statement: str
    ) -> str:
        """Generate casual style explanation."""
        parts = [headline]
        
        # Add emotional match
        if self.config.include_emotional_signal:
            parts.append(f"This song {emotional_match}.")
        
        # Add secondary factors
        if len(factors) > 1:
            secondary = [f.description for f in factors[1:self.config.max_reasons]]
            if secondary:
                parts.append(f"It's also {' and '.join(secondary)}.")
        
        # Add confidence if enabled
        if self.config.include_confidence:
            parts.append(confidence_statement + ".")
        
        return " ".join(parts)
    
    def _generate_detailed_explanation(
        self,
        song: Dict[str, Any],
        headline: str,
        emotional_match: str,
        factors: List[ExplanationFactor],
        confidence_statement: str,
        signal: EmotionalSignal
    ) -> str:
        """Generate detailed technical explanation."""
        
        # Factor breakdown
        factor_lines = []
        for i, f in enumerate(factors, 1):
            factor_lines.append(
                f"{i}. {f.factor_type.capitalize()}: {f.description} "
                f"(score: {f.score:.0%}, weight: {f.weight:.0%})"
            )
        factor_breakdown = "\n".join(factor_lines)
        
        # Get song VA if available
        valence = song.get('valence', 0.0)
        arousal = song.get('arousal', song.get('energy', 0.0))
        
        # Calculate emotion score
        emotion_score = factors[0].score if factors else 0.5
        
        return self.templates.DETAILED_TEMPLATE.format(
            song_name=song.get('song_name', song.get('name', 'Unknown')),
            artist=song.get('artist', 'Unknown'),
            primary_factor=factors[0].description if factors else "Overall match",
            detected_mood=signal.detected_mood,
            mood_confidence=signal.confidence,
            valence=valence,
            arousal=arousal,
            emotion_score=emotion_score,
            factor_breakdown=factor_breakdown,
            overall_confidence=sum(f.weight * f.score for f in factors) / max(sum(f.weight for f in factors), 1),
            confidence_reasoning=confidence_statement,
        )
    
    def _generate_emotional_explanation(
        self,
        song: Dict[str, Any],
        headline: str,
        emotional_match: str,
        signal: EmotionalSignal
    ) -> str:
        """Generate emotionally-focused explanation."""
        parts = [headline]
        
        # Primary focus on emotional connection
        parts.append(f"This song {emotional_match}.")
        
        # Reference detected signals
        if signal.keywords:
            keywords_str = ", ".join(signal.keywords[:2])
            parts.append(f"I picked up on your mention of {keywords_str}.")
        
        if signal.context_phrases:
            parts.append(f"Based on what you shared, this feels right.")
        
        # Emotional validation
        mood_validations = {
            'happy': "Your positive energy deserves music that amplifies it.",
            'sad': "Sometimes we need music that understands our feelings.",
            'calm': "This should help maintain that peaceful state.",
            'excited': "Let's keep that energy going!",
            'anxious': "This might help ease those feelings.",
            'romantic': "Setting the perfect mood for you.",
        }
        
        validation = mood_validations.get(signal.detected_mood.lower())
        if validation:
            parts.append(validation)
        
        return " ".join(parts)
    
    def explain_batch(
        self,
        songs: List[Dict[str, Any]],
        scores_list: List[Dict[str, float]],
        emotional_signal: EmotionalSignal = None,
        context: Dict[str, Any] = None
    ) -> List[RecommendationExplanation]:
        """Generate explanations for multiple recommendations."""
        explanations = []
        
        for song, scores in zip(songs, scores_list):
            explanation = self.explain(
                song=song,
                scores=scores,
                emotional_signal=emotional_signal,
                context=context,
            )
            explanations.append(explanation)
        
        return explanations


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_simple_explanation(
    song: Dict[str, Any],
    mood: str,
    confidence: float = 0.7
) -> str:
    """
    Generate a simple one-liner explanation.
    
    Args:
        song: Song data
        mood: Target mood
        confidence: Confidence score
        
    Returns:
        Simple explanation string
    """
    explainer = ExplainableRecommendation(
        ExplanationConfig(style=ExplanationStyle.MINIMAL)
    )
    
    signal = EmotionalSignal(
        detected_mood=mood,
        confidence=confidence,
        valence=0.0,
        arousal=0.0,
        intensity=0.5,
    )
    
    explanation = explainer.explain(
        song=song,
        scores={'emotion': confidence},
        emotional_signal=signal,
    )
    
    return explanation.full_explanation


def create_explainer(style: str = "casual") -> ExplainableRecommendation:
    """Create an explainer with specified style."""
    style_map = {
        "casual": ExplanationStyle.CASUAL,
        "detailed": ExplanationStyle.DETAILED,
        "minimal": ExplanationStyle.MINIMAL,
        "emotional": ExplanationStyle.EMOTIONAL,
    }
    
    config = ExplanationConfig(
        style=style_map.get(style.lower(), ExplanationStyle.CASUAL)
    )
    
    return ExplainableRecommendation(config)
