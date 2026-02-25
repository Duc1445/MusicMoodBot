"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - CLARIFICATION STRATEGY ENGINE
=============================================================================

Determines the best clarification strategy based on current conversation state.

The strategy engine decides:
- What type of question to ask next
- How deep to probe (surface vs. specific)
- When to give up probing and recommend

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

from .types import (
    DialogueState,
    ConversationSession,
    EmotionalContext,
    CLARITY_THRESHOLD_MEDIUM,
    MAX_TURNS_DEFAULT,
)
from .clarity_scorer import ClarityResult, ClarityComponents

logger = logging.getLogger(__name__)


# =============================================================================
# STRATEGY TYPES
# =============================================================================

@dataclass
class ClarificationStrategy:
    """
    A clarification strategy recommendation.
    """
    # What to ask
    strategy_type: str        # 'probe_mood', 'probe_intensity', 'probe_context', 'confirm', 'recommend'
    
    # Question parameters
    question_category: str    # 'mood', 'intensity', 'context', 'activity', 'confirmation'
    depth_level: int          # 1=surface, 2=deeper, 3=specific
    
    # Question selection hints
    avoid_questions: List[str] = field(default_factory=list)  # Question IDs to avoid
    preferred_questions: List[str] = field(default_factory=list)  # Preferred question IDs
    
    # Confidence
    confidence: float = 0.5
    reason: str = ""
    
    # Fallback
    fallback_strategy: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_type': self.strategy_type,
            'question_category': self.question_category,
            'depth_level': self.depth_level,
            'avoid_questions': self.avoid_questions,
            'preferred_questions': self.preferred_questions,
            'confidence': self.confidence,
            'reason': self.reason,
            'fallback_strategy': self.fallback_strategy,
        }


# =============================================================================
# STRATEGY ENGINE
# =============================================================================

class ClarificationStrategyEngine:
    """
    Determines the best clarification strategy for the current conversation state.
    
    The engine considers:
    - Current FSM state
    - Clarity score and components
    - Turn history
    - User preferences (if available)
    
    Usage:
        engine = ClarificationStrategyEngine()
        strategy = engine.determine_strategy(session, clarity_result)
        
        # Use strategy to select question
        question = question_bank.select(
            category=strategy.question_category,
            depth=strategy.depth_level,
            avoid=strategy.avoid_questions
        )
    """
    
    def __init__(self, max_probing_turns: int = 3):
        """
        Initialize strategy engine.
        
        Args:
            max_probing_turns: Maximum turns to spend probing
        """
        self.max_probing_turns = max_probing_turns
    
    def determine_strategy(self, session: ConversationSession,
                          clarity_result: ClarityResult) -> ClarificationStrategy:
        """
        Determine the best clarification strategy.
        
        Args:
            session: Current conversation session
            clarity_result: Result from clarity scoring
            
        Returns:
            ClarificationStrategy recommendation
        """
        state = session.state
        turn_count = session.turn_count
        context = session.emotional_context
        
        # Check termination conditions first
        if self._should_recommend(session, clarity_result):
            return self._create_recommend_strategy(clarity_result)
        
        # State-based strategy selection
        if state == DialogueState.GREETING:
            return self._greeting_strategy(session, clarity_result)
        
        elif state == DialogueState.PROBING_MOOD:
            return self._mood_probing_strategy(session, clarity_result)
        
        elif state == DialogueState.PROBING_INTENSITY:
            return self._intensity_probing_strategy(session, clarity_result)
        
        elif state == DialogueState.PROBING_CONTEXT:
            return self._context_probing_strategy(session, clarity_result)
        
        elif state == DialogueState.CONFIRMING:
            return self._confirmation_strategy(session, clarity_result)
        
        else:
            # Default: recommend
            return self._create_recommend_strategy(clarity_result)
    
    def _should_recommend(self, session: ConversationSession,
                         clarity_result: ClarityResult) -> bool:
        """
        Check if we should skip probing and recommend.
        """
        # Already ready
        if clarity_result.can_recommend:
            return True
        
        # Max turns reached
        if session.turn_count >= session.max_turns:
            return True
        
        # User preference for brief interactions
        # (This would come from user settings)
        # if session.user_prefs.conversation_style == 'brief' and session.turn_count >= 2:
        #     return True
        
        return False
    
    def _greeting_strategy(self, session: ConversationSession,
                          clarity: ClarityResult) -> ClarificationStrategy:
        """
        Strategy after greeting state.
        """
        # If mood was detected in greeting, go to intensity
        if clarity.components.mood_specified:
            return ClarificationStrategy(
                strategy_type='probe_intensity',
                question_category='intensity',
                depth_level=1,
                confidence=0.8,
                reason="Mood detected in greeting, probe for intensity",
            )
        
        # Otherwise, ask about mood
        return ClarificationStrategy(
            strategy_type='probe_mood',
            question_category='mood',
            depth_level=1,
            preferred_questions=['mood_general_01', 'mood_general_02'],
            confidence=0.9,
            reason="No mood detected, ask about mood",
        )
    
    def _mood_probing_strategy(self, session: ConversationSession,
                               clarity: ClarityResult) -> ClarificationStrategy:
        """
        Strategy when probing for mood.
        """
        context = session.emotional_context
        
        # If we have some mood signal but low confidence
        if clarity.components.mood_confidence > 0 and clarity.components.mood_confidence < 0.6:
            # Ask deeper questions to clarify
            return ClarificationStrategy(
                strategy_type='probe_mood',
                question_category='mood',
                depth_level=2,
                preferred_questions=['mood_deeper_01', 'mood_deeper_02'],
                confidence=0.7,
                reason="Low confidence mood, probe deeper",
            )
        
        # If mood history shows inconsistency
        if context.consistency_score < 0.5 and len(context.mood_history) >= 2:
            return ClarificationStrategy(
                strategy_type='probe_mood',
                question_category='mood',
                depth_level=2,
                confidence=0.6,
                reason="Inconsistent mood signals, clarify",
            )
        
        # Default surface-level mood question
        return ClarificationStrategy(
            strategy_type='probe_mood',
            question_category='mood',
            depth_level=1,
            avoid_questions=self._get_asked_questions(session),
            confidence=0.8,
            reason="Need mood information",
        )
    
    def _intensity_probing_strategy(self, session: ConversationSession,
                                    clarity: ClarityResult) -> ClarificationStrategy:
        """
        Strategy when probing for intensity.
        """
        # If we have reasonable clarity already, might skip intensity
        if clarity.score >= CLARITY_THRESHOLD_MEDIUM:
            return ClarificationStrategy(
                strategy_type='confirm',
                question_category='confirmation',
                depth_level=1,
                confidence=0.7,
                reason="Good clarity, confirm before recommending",
            )
        
        return ClarificationStrategy(
            strategy_type='probe_intensity',
            question_category='intensity',
            depth_level=1,
            preferred_questions=['intensity_01', 'intensity_02'],
            avoid_questions=self._get_asked_questions(session),
            confidence=0.8,
            reason="Need intensity information",
        )
    
    def _context_probing_strategy(self, session: ConversationSession,
                                  clarity: ClarityResult) -> ClarificationStrategy:
        """
        Strategy when probing for context.
        """
        context = session.emotional_context
        
        # Determine what context is missing
        if not context.context.activity:
            return ClarificationStrategy(
                strategy_type='probe_context',
                question_category='activity',
                depth_level=1,
                preferred_questions=['context_activity_01', 'context_activity_02'],
                confidence=0.7,
                reason="Missing activity context",
            )
        
        if not context.context.time_of_day:
            return ClarificationStrategy(
                strategy_type='probe_context',
                question_category='time',
                depth_level=1,
                preferred_questions=['context_time_01'],
                confidence=0.6,
                reason="Missing time context",
            )
        
        # Context is sufficient, move to confirm
        return ClarificationStrategy(
            strategy_type='confirm',
            question_category='confirmation',
            depth_level=1,
            confidence=0.8,
            reason="Context sufficient, confirm",
        )
    
    def _confirmation_strategy(self, session: ConversationSession,
                               clarity: ClarityResult) -> ClarificationStrategy:
        """
        Strategy when confirming understanding.
        """
        return ClarificationStrategy(
            strategy_type='confirm',
            question_category='confirmation',
            depth_level=1,
            preferred_questions=['confirm_mood_01', 'confirm_mood_02'],
            confidence=0.9,
            reason="Ready to confirm mood/intensity",
        )
    
    def _create_recommend_strategy(self, clarity: ClarityResult) -> ClarificationStrategy:
        """
        Create a strategy to proceed with recommendations.
        """
        return ClarificationStrategy(
            strategy_type='recommend',
            question_category='none',
            depth_level=0,
            confidence=clarity.score,
            reason=f"Ready to recommend (clarity: {clarity.score:.2f})",
        )
    
    def _get_asked_questions(self, session: ConversationSession) -> List[str]:
        """
        Get list of question IDs already asked in this session.
        """
        asked = []
        for turn in session.turns:
            if turn.question_asked:
                asked.append(turn.question_asked)
        return asked
    
    def get_probing_depth(self, session: ConversationSession) -> int:
        """
        Determine appropriate probing depth based on turn count.
        """
        turn_count = session.turn_count
        
        if turn_count <= 1:
            return 1  # Surface
        elif turn_count <= 3:
            return 2  # Deeper
        else:
            return 3  # Specific


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_strategy_engine(max_probing_turns: int = 3) -> ClarificationStrategyEngine:
    """
    Create a ClarificationStrategyEngine instance.
    """
    return ClarificationStrategyEngine(max_probing_turns=max_probing_turns)
