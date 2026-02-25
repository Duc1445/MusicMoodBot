"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - DIALOGUE STATE MACHINE
=============================================================================

Finite State Machine (FSM) implementation for dialogue flow control.

The DialogueFSM manages state transitions in the conversation, determining
when to probe for more information vs. proceed to recommendations.

State Transition Diagram:
┌─────────────────────────────────────────────────────────────────────────┐
│                        DIALOGUE STATE MACHINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐                                                          │
│  │ GREETING │──────────────────┐                                       │
│  └────┬─────┘                  │                                       │
│       │ no_mood                │ has_mood (high conf)                  │
│       ▼                        │                                       │
│  ┌─────────────┐               │                                       │
│  │PROBING_MOOD │◄──────────────┼───────────────────┐                   │
│  └──────┬──────┘               │                   │                   │
│         │ mood_detected        │                   │ correction        │
│         ▼                      │                   │                   │
│  ┌──────────────────┐          │                   │                   │
│  │PROBING_INTENSITY │──────────┤                   │                   │
│  └────────┬─────────┘          │                   │                   │
│           │ intensity_set      │                   │                   │
│           ▼                    │                   │                   │
│  ┌──────────────────┐          │                   │                   │
│  │ PROBING_CONTEXT  │──────────┤                   │                   │
│  └────────┬─────────┘          │                   │                   │
│           │ context_clear      │                   │                   │
│           ▼                    ▼                   │                   │
│  ┌──────────────┐    ┌────────────────┐           │                   │
│  │  CONFIRMING  │───►│ RECOMMENDING   │───────────┴─────┐             │
│  └──────────────┘    └───────┬────────┘                 │             │
│                              │                          │             │
│                              ▼                          │             │
│                      ┌────────────┐                     │             │
│                      │  FEEDBACK  │─────────────────────┘             │
│                      └─────┬──────┘                                   │
│                            │                                          │
│                            ▼                                          │
│  ┌─────────┐        ┌──────────┐        ┌──────────┐                 │
│  │ TIMEOUT │        │  ENDED   │        │ ABORTED  │                 │
│  └─────────┘        └──────────┘        └──────────┘                 │
│                                                                       │
└─────────────────────────────────────────────────────────────────────────┘

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
import re

from .types import (
    DialogueState,
    ConversationSession,
    ConversationTurn,
    EmotionalContext,
    EmotionalSignals,
    Intent,
    CLARITY_THRESHOLD_HIGH,
    CLARITY_THRESHOLD_MEDIUM,
    MAX_TURNS_DEFAULT,
)

logger = logging.getLogger(__name__)


# =============================================================================
# TRANSITION DATA STRUCTURES
# =============================================================================

@dataclass
class Transition:
    """
    Represents a state transition in the FSM.
    
    Attributes:
        from_state: Source state
        to_state: Target state
        guard: Callable that returns True if transition is allowed
        priority: Lower number = higher priority (checked first)
        name: Human-readable name for logging
    """
    from_state: DialogueState
    to_state: DialogueState
    guard: Callable[[ConversationSession, Optional[ConversationTurn]], bool]
    priority: int = 5
    name: str = ""
    
    def can_transition(self, session: ConversationSession, 
                       turn: Optional[ConversationTurn] = None) -> bool:
        """Check if this transition is valid given current state."""
        try:
            return self.guard(session, turn)
        except Exception as e:
            logger.warning(f"Guard {self.name} raised exception: {e}")
            return False


@dataclass
class TransitionResult:
    """
    Result of attempting a state transition.
    """
    success: bool
    from_state: DialogueState
    to_state: DialogueState
    transition_name: str = ""
    reason: str = ""


# =============================================================================
# GUARD FUNCTIONS
# =============================================================================
# Guards are predicates that determine if a transition should be taken.
# They receive the current session and optionally the current turn.

def guard_always_true(session: ConversationSession, 
                      turn: Optional[ConversationTurn] = None) -> bool:
    """Always allow transition."""
    return True


def guard_has_high_confidence_mood(session: ConversationSession,
                                   turn: Optional[ConversationTurn] = None) -> bool:
    """
    Allow transition if we have a high-confidence mood detection.
    
    Conditions:
    - Primary mood is set
    - Confidence >= CLARITY_THRESHOLD_HIGH (0.8)
    """
    ctx = session.emotional_context
    return (
        ctx.primary_mood is not None and
        ctx.mood_confidence >= CLARITY_THRESHOLD_HIGH
    )


def guard_has_medium_confidence_mood(session: ConversationSession,
                                     turn: Optional[ConversationTurn] = None) -> bool:
    """
    Allow transition if we have at least medium-confidence mood.
    
    Conditions:
    - Primary mood is set
    - Confidence >= CLARITY_THRESHOLD_MEDIUM (0.6)
    """
    ctx = session.emotional_context
    return (
        ctx.primary_mood is not None and
        ctx.mood_confidence >= CLARITY_THRESHOLD_MEDIUM
    )


def guard_mood_detected(session: ConversationSession,
                        turn: Optional[ConversationTurn] = None) -> bool:
    """
    Allow transition if any mood was detected (regardless of confidence).
    """
    if turn and turn.detected_mood:
        return True
    return session.emotional_context.primary_mood is not None


def guard_needs_intensity(session: ConversationSession,
                          turn: Optional[ConversationTurn] = None) -> bool:
    """
    Allow transition if mood is set but intensity is not.
    """
    ctx = session.emotional_context
    return (
        ctx.primary_mood is not None and
        not ctx.intensity_specified
    )


def guard_intensity_set(session: ConversationSession,
                        turn: Optional[ConversationTurn] = None) -> bool:
    """
    Allow transition if intensity has been determined.
    """
    ctx = session.emotional_context
    return ctx.intensity_specified or ctx.primary_intensity is not None


def guard_needs_context(session: ConversationSession,
                        turn: Optional[ConversationTurn] = None) -> bool:
    """
    Allow transition if context is needed for better recommendations.
    
    Context is needed if:
    - Context richness is low (< 0.3)
    - We haven't exceeded max probing attempts
    """
    ctx = session.emotional_context
    return (
        ctx.context_richness < 0.3 and
        ctx.clarification_attempts < 2
    )


def guard_context_clear(session: ConversationSession,
                        turn: Optional[ConversationTurn] = None) -> bool:
    """
    Allow transition if we have enough context or hit probing limit.
    """
    ctx = session.emotional_context
    return (
        ctx.context_richness >= 0.3 or
        ctx.clarification_attempts >= 2
    )


def guard_ready_to_recommend(session: ConversationSession,
                             turn: Optional[ConversationTurn] = None) -> bool:
    """
    Check if we're ready to generate recommendations.
    
    Ready when:
    - Have mood with sufficient confidence
    - OR hit max turns
    - OR user requested skip
    """
    ctx = session.emotional_context
    
    # Have confident mood
    if ctx.primary_mood and ctx.mood_confidence >= CLARITY_THRESHOLD_MEDIUM:
        return True
    
    # Hit max turns
    if session.turn_count >= session.max_turns:
        return True
    
    # User intent was skip
    if turn and turn.intent == Intent.SKIP:
        return True
    
    return False


def guard_user_confirmed(session: ConversationSession,
                         turn: Optional[ConversationTurn] = None) -> bool:
    """
    Check if user confirmed the detected mood/intention.
    """
    if turn is None:
        return False
    return turn.intent == Intent.CONFIRMATION


def guard_user_negated(session: ConversationSession,
                       turn: Optional[ConversationTurn] = None) -> bool:
    """
    Check if user negated/denied the detected mood.
    """
    if turn is None:
        return False
    return turn.intent in (Intent.NEGATION, Intent.MOOD_CORRECTION)


def guard_max_turns_reached(session: ConversationSession,
                            turn: Optional[ConversationTurn] = None) -> bool:
    """
    Check if max turns have been reached.
    """
    return session.turn_count >= session.max_turns


def guard_is_greeting_only(session: ConversationSession,
                           turn: Optional[ConversationTurn] = None) -> bool:
    """
    Check if the input is a greeting without mood information.
    """
    if turn is None:
        return True  # Initial state, treat as greeting
    return turn.intent == Intent.GREETING and turn.detected_mood is None


def guard_is_mood_correction(session: ConversationSession,
                             turn: Optional[ConversationTurn] = None) -> bool:
    """
    Check if user is correcting previously detected mood.
    """
    if turn is None:
        return False
    return turn.intent == Intent.MOOD_CORRECTION


def guard_feedback_received(session: ConversationSession,
                            turn: Optional[ConversationTurn] = None) -> bool:
    """
    Check if feedback was given on recommendations.
    """
    if turn is None:
        return False
    return turn.intent in (Intent.FEEDBACK_POSITIVE, Intent.FEEDBACK_NEGATIVE)


def guard_wants_more_recommendations(session: ConversationSession,
                                     turn: Optional[ConversationTurn] = None) -> bool:
    """
    Check if user wants more recommendations.
    """
    if turn is None:
        return False
    
    # Check for patterns indicating wanting more
    if turn.user_input:
        more_patterns = [
            r'\bthêm\b', r'\bmore\b', r'\btiếp\b', r'\bnữa\b',
            r'\bkhác\b', r'\banother\b', r'\bkhông thích\b',
        ]
        text = turn.user_input.lower()
        return any(re.search(p, text) for p in more_patterns)
    
    return False


def guard_skip_requested(session: ConversationSession,
                         turn: Optional[ConversationTurn] = None) -> bool:
    """
    Check if user wants to skip probing and get recommendations.
    """
    if turn is None:
        return False
    
    if turn.intent == Intent.SKIP:
        return True
    
    # Check for skip patterns
    if turn.user_input:
        skip_patterns = [
            r'\bskip\b', r'\bbỏ qua\b', r'\bchơi ngay\b', r'\bplay\b',
            r'\bnghe ngay\b', r'\bđi thôi\b', r'\blet.s go\b',
        ]
        text = turn.user_input.lower()
        return any(re.search(p, text) for p in skip_patterns)
    
    return False


# =============================================================================
# DIALOGUE FSM
# =============================================================================

class DialogueFSM:
    """
    Finite State Machine for managing conversation dialogue flow.
    
    The FSM determines:
    1. What state the conversation is in
    2. What state to transition to based on user input
    3. When to probe for more information vs. recommend
    
    Usage:
        fsm = DialogueFSM()
        session = ConversationSession(...)
        
        # Process user turn
        turn = ConversationTurn(...)
        result = fsm.process_turn(session, turn)
        
        # Get next action
        action = fsm.get_next_action(session)
    """
    
    def __init__(self, max_turns: int = MAX_TURNS_DEFAULT):
        """
        Initialize the dialogue FSM.
        
        Args:
            max_turns: Maximum turns before forcing recommendations
        """
        self.max_turns = max_turns
        self._transitions: Dict[DialogueState, List[Transition]] = {}
        self._define_transitions()
    
    def _define_transitions(self):
        """
        Define all state transitions with their guards.
        
        Transitions are checked in priority order (lower number = higher priority).
        The first transition whose guard returns True is taken.
        """
        
        # =====================================================================
        # FROM: GREETING
        # =====================================================================
        self._add_transition(
            DialogueState.GREETING,
            DialogueState.RECOMMENDING,
            guard_has_high_confidence_mood,
            priority=1,
            name="greeting_to_recommend_high_conf"
        )
        self._add_transition(
            DialogueState.GREETING,
            DialogueState.CONFIRMING,
            guard_has_medium_confidence_mood,
            priority=2,
            name="greeting_to_confirm_medium_conf"
        )
        self._add_transition(
            DialogueState.GREETING,
            DialogueState.PROBING_INTENSITY,
            guard_mood_detected,
            priority=3,
            name="greeting_to_intensity"
        )
        self._add_transition(
            DialogueState.GREETING,
            DialogueState.PROBING_MOOD,
            guard_is_greeting_only,
            priority=10,
            name="greeting_to_probe_mood"
        )
        
        # =====================================================================
        # FROM: PROBING_MOOD
        # =====================================================================
        self._add_transition(
            DialogueState.PROBING_MOOD,
            DialogueState.RECOMMENDING,
            guard_skip_requested,
            priority=1,
            name="probe_mood_skip_to_recommend"
        )
        self._add_transition(
            DialogueState.PROBING_MOOD,
            DialogueState.RECOMMENDING,
            guard_has_high_confidence_mood,
            priority=2,
            name="probe_mood_to_recommend"
        )
        self._add_transition(
            DialogueState.PROBING_MOOD,
            DialogueState.CONFIRMING,
            guard_has_medium_confidence_mood,
            priority=3,
            name="probe_mood_to_confirm"
        )
        self._add_transition(
            DialogueState.PROBING_MOOD,
            DialogueState.PROBING_INTENSITY,
            guard_mood_detected,
            priority=4,
            name="probe_mood_to_intensity"
        )
        self._add_transition(
            DialogueState.PROBING_MOOD,
            DialogueState.RECOMMENDING,
            guard_max_turns_reached,
            priority=5,
            name="probe_mood_max_turns"
        )
        
        # =====================================================================
        # FROM: PROBING_INTENSITY
        # =====================================================================
        self._add_transition(
            DialogueState.PROBING_INTENSITY,
            DialogueState.RECOMMENDING,
            guard_skip_requested,
            priority=1,
            name="probe_intensity_skip"
        )
        self._add_transition(
            DialogueState.PROBING_INTENSITY,
            DialogueState.CONFIRMING,
            guard_intensity_set,
            priority=2,
            name="probe_intensity_to_confirm"
        )
        self._add_transition(
            DialogueState.PROBING_INTENSITY,
            DialogueState.PROBING_CONTEXT,
            guard_context_clear,
            priority=3,
            name="probe_intensity_to_context"
        )
        self._add_transition(
            DialogueState.PROBING_INTENSITY,
            DialogueState.RECOMMENDING,
            guard_max_turns_reached,
            priority=10,
            name="probe_intensity_max_turns"
        )
        
        # =====================================================================
        # FROM: PROBING_CONTEXT
        # =====================================================================
        self._add_transition(
            DialogueState.PROBING_CONTEXT,
            DialogueState.RECOMMENDING,
            guard_skip_requested,
            priority=1,
            name="probe_context_skip"
        )
        self._add_transition(
            DialogueState.PROBING_CONTEXT,
            DialogueState.CONFIRMING,
            guard_context_clear,
            priority=2,
            name="probe_context_to_confirm"
        )
        self._add_transition(
            DialogueState.PROBING_CONTEXT,
            DialogueState.RECOMMENDING,
            guard_max_turns_reached,
            priority=10,
            name="probe_context_max_turns"
        )
        
        # =====================================================================
        # FROM: CONFIRMING
        # =====================================================================
        self._add_transition(
            DialogueState.CONFIRMING,
            DialogueState.RECOMMENDING,
            guard_user_confirmed,
            priority=1,
            name="confirm_to_recommend"
        )
        self._add_transition(
            DialogueState.CONFIRMING,
            DialogueState.PROBING_MOOD,
            guard_user_negated,
            priority=2,
            name="confirm_negated_to_probe"
        )
        self._add_transition(
            DialogueState.CONFIRMING,
            DialogueState.RECOMMENDING,
            guard_max_turns_reached,
            priority=10,
            name="confirm_max_turns"
        )
        # Default: No explicit confirmation, proceed with recommendation
        self._add_transition(
            DialogueState.CONFIRMING,
            DialogueState.RECOMMENDING,
            guard_ready_to_recommend,
            priority=5,
            name="confirm_ready_recommend"
        )
        
        # =====================================================================
        # FROM: RECOMMENDING
        # =====================================================================
        self._add_transition(
            DialogueState.RECOMMENDING,
            DialogueState.FEEDBACK,
            guard_always_true,
            priority=1,
            name="recommend_to_feedback"
        )
        
        # =====================================================================
        # FROM: FEEDBACK
        # =====================================================================
        self._add_transition(
            DialogueState.FEEDBACK,
            DialogueState.RECOMMENDING,
            guard_wants_more_recommendations,
            priority=1,
            name="feedback_more_recommendations"
        )
        self._add_transition(
            DialogueState.FEEDBACK,
            DialogueState.PROBING_MOOD,
            guard_is_mood_correction,
            priority=2,
            name="feedback_mood_correction"
        )
        self._add_transition(
            DialogueState.FEEDBACK,
            DialogueState.ENDED,
            guard_feedback_received,
            priority=3,
            name="feedback_to_ended"
        )
    
    def _add_transition(self, from_state: DialogueState, to_state: DialogueState,
                        guard: Callable, priority: int = 5, name: str = ""):
        """Add a transition to the FSM."""
        if from_state not in self._transitions:
            self._transitions[from_state] = []
        
        transition = Transition(
            from_state=from_state,
            to_state=to_state,
            guard=guard,
            priority=priority,
            name=name or f"{from_state.name}_to_{to_state.name}"
        )
        self._transitions[from_state].append(transition)
        
        # Keep sorted by priority
        self._transitions[from_state].sort(key=lambda t: t.priority)
    
    def get_valid_transitions(self, session: ConversationSession,
                              turn: Optional[ConversationTurn] = None) -> List[Transition]:
        """
        Get all valid transitions from current state.
        
        Returns transitions that pass their guard conditions, sorted by priority.
        """
        current_state = session.state
        possible = self._transitions.get(current_state, [])
        
        valid = []
        for t in possible:
            if t.can_transition(session, turn):
                valid.append(t)
        
        return valid
    
    def compute_next_state(self, session: ConversationSession,
                           turn: Optional[ConversationTurn] = None) -> TransitionResult:
        """
        Compute the next state based on current session and turn.
        
        Args:
            session: Current conversation session
            turn: Optional current turn being processed
            
        Returns:
            TransitionResult with success, states, and reason
        """
        current_state = session.state
        valid_transitions = self.get_valid_transitions(session, turn)
        
        if not valid_transitions:
            # No valid transition, stay in current state
            logger.debug(f"No valid transitions from {current_state.name}")
            return TransitionResult(
                success=False,
                from_state=current_state,
                to_state=current_state,
                reason="No valid transitions"
            )
        
        # Take the highest priority (lowest number) valid transition
        best = valid_transitions[0]
        
        logger.debug(f"Transition: {best.name} ({current_state.name} -> {best.to_state.name})")
        
        return TransitionResult(
            success=True,
            from_state=current_state,
            to_state=best.to_state,
            transition_name=best.name,
            reason=f"Guard '{best.name}' passed"
        )
    
    def apply_transition(self, session: ConversationSession,
                         turn: Optional[ConversationTurn] = None) -> TransitionResult:
        """
        Compute and apply the next state transition.
        
        This modifies session.state if a valid transition is found.
        
        Args:
            session: Current conversation session
            turn: Optional current turn being processed
            
        Returns:
            TransitionResult
        """
        result = self.compute_next_state(session, turn)
        
        if result.success:
            session.state = result.to_state
            logger.info(f"State transition: {result.from_state.name} -> {result.to_state.name} "
                       f"({result.transition_name})")
        
        return result
    
    def process_turn(self, session: ConversationSession,
                     turn: ConversationTurn) -> TransitionResult:
        """
        Process a conversation turn and determine state transition.
        
        This is the main entry point for FSM processing.
        
        Args:
            session: Current conversation session
            turn: Current turn being processed
            
        Returns:
            TransitionResult
        """
        # Record state before
        turn.state_before = session.state
        
        # Apply transition
        result = self.apply_transition(session, turn)
        
        # Record state after
        turn.state_after = session.state
        
        return result
    
    def get_state_action(self, state: DialogueState) -> str:
        """
        Get the recommended action for a given state.
        
        Returns:
            Action type: 'probe_mood', 'probe_intensity', 'probe_context',
                        'confirm', 'recommend', 'collect_feedback', 'end'
        """
        action_map = {
            DialogueState.GREETING: 'greet',
            DialogueState.PROBING_MOOD: 'probe_mood',
            DialogueState.PROBING_INTENSITY: 'probe_intensity',
            DialogueState.PROBING_CONTEXT: 'probe_context',
            DialogueState.CONFIRMING: 'confirm',
            DialogueState.RECOMMENDING: 'recommend',
            DialogueState.FEEDBACK: 'collect_feedback',
            DialogueState.ENDED: 'end',
            DialogueState.TIMEOUT: 'end',
            DialogueState.ABORTED: 'end',
        }
        return action_map.get(state, 'unknown')
    
    def is_terminal_state(self, state: DialogueState) -> bool:
        """Check if state is a terminal state (session should end)."""
        return state in (
            DialogueState.ENDED,
            DialogueState.TIMEOUT,
            DialogueState.ABORTED,
        )
    
    def should_recommend(self, session: ConversationSession) -> bool:
        """Check if we should proceed to recommendation."""
        return session.state in (
            DialogueState.RECOMMENDING,
            DialogueState.FEEDBACK,
        ) or guard_ready_to_recommend(session)
    
    def reset(self, session: ConversationSession):
        """Reset session to initial state (for re-evaluation)."""
        session.state = DialogueState.GREETING
        logger.info(f"Session {session.session_id} reset to GREETING")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_default_fsm() -> DialogueFSM:
    """
    Create a DialogueFSM with default configuration.
    """
    return DialogueFSM(max_turns=MAX_TURNS_DEFAULT)
