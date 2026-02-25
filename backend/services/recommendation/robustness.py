"""
=============================================================================
ROBUSTNESS & EDGE CASE HANDLING
=============================================================================

Production-grade safeguards for the recommendation system.

Features:
=========

1. Max Turn Safeguard:
   - Prevent infinite conversation loops
   - Force recommendation after MAX_TURNS
   
2. Confidence Decay:
   - time_factor = exp(-λ * time_since_last_turn)
   - Reduce confidence for stale sessions
   
3. Contradictory Mood Resolution:
   - Weighted majority voting
   - Recency bias for mood selection
   
4. Timeout Handling:
   - Session expiration
   - Graceful degradation
   
5. Idempotent Processing:
   - Request deduplication
   - Replay protection
   
6. FSM Error Transitions:
   - Safe fallback states
   - Error recovery

Author: MusicMoodBot Team
Version: 3.1.0
=============================================================================
"""

from __future__ import annotations

import hashlib
import logging
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Set, Any
from functools import wraps

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class RobustnessConfig:
    """Configuration for robustness features."""
    
    # Max turn safeguard
    max_turns: int = 15
    force_recommendation_at: int = 12  # Force recommendation at this turn
    warning_at_turn: int = 10
    
    # Confidence decay
    decay_lambda: float = 0.05  # Decay rate per minute
    min_confidence_after_decay: float = 0.1
    decay_grace_period_seconds: float = 30.0  # No decay within this period
    
    # Timeout
    session_timeout_seconds: float = 1800.0  # 30 minutes
    inactivity_timeout_seconds: float = 300.0  # 5 minutes
    
    # Idempotency
    request_cache_ttl_seconds: float = 60.0
    max_cached_requests: int = 1000
    
    # Error handling
    max_consecutive_errors: int = 3
    error_cooldown_seconds: float = 5.0


# =============================================================================
# MAX TURN SAFEGUARD
# =============================================================================

class TurnSafeguard:
    """
    Prevents infinite conversation loops.
    
    Behavior:
    - Warning at warning_at_turn
    - Force recommendation at force_recommendation_at
    - Hard stop at max_turns
    
    Usage:
        safeguard = TurnSafeguard(config)
        result = safeguard.check_turn(session_id, current_turn)
        
        if result.should_force_recommendation:
            # Trigger recommendation immediately
        elif result.should_warn:
            # Add warning to response
    """
    
    @dataclass
    class CheckResult:
        """Result of turn check."""
        allowed: bool = True
        should_warn: bool = False
        should_force_recommendation: bool = False
        should_terminate: bool = False
        message: Optional[str] = None
        remaining_turns: int = 0
    
    def __init__(self, config: RobustnessConfig = None):
        self.config = config or RobustnessConfig()
        self._session_turns: Dict[str, int] = {}
    
    def check_turn(self, session_id: str, current_turn: int) -> CheckResult:
        """
        Check if turn should be allowed.
        
        Args:
            session_id: Session identifier
            current_turn: Current turn number
            
        Returns:
            CheckResult with action flags
        """
        self._session_turns[session_id] = current_turn
        remaining = self.config.max_turns - current_turn
        
        # Hard limit exceeded
        if current_turn >= self.config.max_turns:
            return self.CheckResult(
                allowed=False,
                should_terminate=True,
                message=f"Maximum turns ({self.config.max_turns}) reached. Session ended.",
                remaining_turns=0,
            )
        
        # Force recommendation threshold
        if current_turn >= self.config.force_recommendation_at:
            return self.CheckResult(
                allowed=True,
                should_force_recommendation=True,
                message="Let me make a recommendation based on our conversation so far.",
                remaining_turns=remaining,
            )
        
        # Warning threshold
        if current_turn >= self.config.warning_at_turn:
            return self.CheckResult(
                allowed=True,
                should_warn=True,
                message=f"We have {remaining} turns remaining to find your perfect song.",
                remaining_turns=remaining,
            )
        
        return self.CheckResult(
            allowed=True,
            remaining_turns=remaining,
        )
    
    def reset_session(self, session_id: str) -> None:
        """Reset turn count for session."""
        self._session_turns.pop(session_id, None)


# =============================================================================
# CONFIDENCE DECAY
# =============================================================================

class ConfidenceDecay:
    """
    Time-based confidence decay for stale sessions.
    
    Formula:
        decayed_confidence = confidence * exp(-λ * t)
        
    Where:
        λ = decay rate per minute
        t = minutes since last activity
        
    Usage:
        decay = ConfidenceDecay(config)
        new_confidence = decay.apply(
            confidence=0.8,
            last_activity=datetime.now() - timedelta(minutes=10)
        )
    """
    
    def __init__(self, config: RobustnessConfig = None):
        self.config = config or RobustnessConfig()
    
    def apply(
        self,
        confidence: float,
        last_activity: datetime,
        current_time: datetime = None
    ) -> float:
        """
        Apply confidence decay.
        
        Args:
            confidence: Original confidence value [0, 1]
            last_activity: Time of last activity
            current_time: Current time (defaults to now)
            
        Returns:
            Decayed confidence value
        """
        current_time = current_time or datetime.now()
        elapsed_seconds = (current_time - last_activity).total_seconds()
        
        # Grace period - no decay
        if elapsed_seconds <= self.config.decay_grace_period_seconds:
            return confidence
        
        # Convert to minutes for decay calculation
        elapsed_minutes = (elapsed_seconds - self.config.decay_grace_period_seconds) / 60.0
        
        # Apply exponential decay
        decay_factor = math.exp(-self.config.decay_lambda * elapsed_minutes)
        decayed = confidence * decay_factor
        
        # Apply minimum threshold
        return max(decayed, self.config.min_confidence_after_decay)
    
    def get_decay_factor(
        self,
        last_activity: datetime,
        current_time: datetime = None
    ) -> float:
        """Get decay factor without applying to confidence."""
        current_time = current_time or datetime.now()
        elapsed_seconds = (current_time - last_activity).total_seconds()
        
        if elapsed_seconds <= self.config.decay_grace_period_seconds:
            return 1.0
        
        elapsed_minutes = (elapsed_seconds - self.config.decay_grace_period_seconds) / 60.0
        return math.exp(-self.config.decay_lambda * elapsed_minutes)


# =============================================================================
# CONTRADICTORY MOOD RESOLUTION
# =============================================================================

@dataclass
class MoodObservation:
    """A single mood observation."""
    mood: str
    confidence: float
    timestamp: datetime
    source: str = "user_input"  # user_input, emotion_detection, explicit


class ContradictoryMoodResolver:
    """
    Resolves conflicting mood signals using weighted voting.
    
    Algorithm:
    1. Apply recency weight to each observation
    2. Apply source weight (explicit > user_input > emotion_detection)
    3. Apply confidence weight
    4. Aggregate by mood category
    5. Return highest scoring mood
    
    Formula:
        mood_score = Σ (confidence_i * recency_weight_i * source_weight_i)
        
    Where:
        recency_weight = exp(-λ * age_in_minutes)
        source_weight = {explicit: 1.5, user_input: 1.0, emotion_detection: 0.7}
    
    Usage:
        resolver = ContradictoryMoodResolver()
        resolver.add_observation("happy", 0.8)
        resolver.add_observation("sad", 0.6)  # Contradictory!
        
        result = resolver.resolve()
        # result.mood = "happy" (higher confidence wins)
    """
    
    SOURCE_WEIGHTS = {
        "explicit": 1.5,
        "user_input": 1.0,
        "emotion_detection": 0.7,
        "context_inference": 0.5,
    }
    
    RECENCY_LAMBDA = 0.1  # Decay per minute
    
    @dataclass
    class Resolution:
        """Result of mood resolution."""
        mood: str
        confidence: float
        contributing_observations: int
        was_contradictory: bool
        alternative_moods: List[Tuple[str, float]]  # [(mood, score), ...]
    
    def __init__(self):
        self.observations: List[MoodObservation] = []
    
    def add_observation(
        self,
        mood: str,
        confidence: float,
        source: str = "user_input",
        timestamp: datetime = None
    ) -> None:
        """Add a mood observation."""
        self.observations.append(MoodObservation(
            mood=mood.lower(),
            confidence=max(0.0, min(1.0, confidence)),
            timestamp=timestamp or datetime.now(),
            source=source,
        ))
    
    def resolve(self, current_time: datetime = None) -> Resolution:
        """
        Resolve potentially contradictory moods.
        
        Returns:
            Resolution with selected mood and confidence
        """
        if not self.observations:
            return self.Resolution(
                mood="neutral",
                confidence=0.0,
                contributing_observations=0,
                was_contradictory=False,
                alternative_moods=[],
            )
        
        current_time = current_time or datetime.now()
        mood_scores: Dict[str, float] = defaultdict(float)
        mood_counts: Dict[str, int] = defaultdict(int)
        
        for obs in self.observations:
            # Calculate recency weight
            age_minutes = (current_time - obs.timestamp).total_seconds() / 60.0
            recency_weight = math.exp(-self.RECENCY_LAMBDA * age_minutes)
            
            # Get source weight
            source_weight = self.SOURCE_WEIGHTS.get(obs.source, 0.5)
            
            # Calculate weighted score
            score = obs.confidence * recency_weight * source_weight
            mood_scores[obs.mood] += score
            mood_counts[obs.mood] += 1
        
        # Sort by score
        sorted_moods = sorted(mood_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_moods:
            return self.Resolution(
                mood="neutral",
                confidence=0.0,
                contributing_observations=len(self.observations),
                was_contradictory=False,
                alternative_moods=[],
            )
        
        best_mood, best_score = sorted_moods[0]
        
        # Normalize confidence to [0, 1]
        max_possible = len(self.observations) * 1.5  # Max source weight
        normalized_confidence = min(1.0, best_score / max_possible if max_possible > 0 else 0)
        
        # Check if contradictory (multiple moods with significant scores)
        was_contradictory = (
            len(sorted_moods) > 1 and 
            sorted_moods[1][1] > 0.3 * best_score
        )
        
        return self.Resolution(
            mood=best_mood,
            confidence=normalized_confidence,
            contributing_observations=mood_counts[best_mood],
            was_contradictory=was_contradictory,
            alternative_moods=sorted_moods[1:4],  # Top 3 alternatives
        )
    
    def clear(self) -> None:
        """Clear all observations."""
        self.observations.clear()


# =============================================================================
# TIMEOUT HANDLING
# =============================================================================

class TimeoutHandler:
    """
    Session and inactivity timeout management.
    
    Provides:
    - Session expiration checking
    - Inactivity detection
    - Graceful session cleanup
    
    Usage:
        handler = TimeoutHandler(config)
        
        # Check session status
        status = handler.check_session(session_id, start_time, last_activity)
        
        if status.expired:
            # Handle expired session
        elif status.inactive:
            # Handle inactive session (maybe send reminder)
    """
    
    class SessionStatus(Enum):
        ACTIVE = auto()
        INACTIVE = auto()
        EXPIRED = auto()
    
    @dataclass
    class CheckResult:
        """Timeout check result."""
        status: 'TimeoutHandler.SessionStatus'
        inactive_seconds: float = 0.0
        session_age_seconds: float = 0.0
        time_until_expiry_seconds: float = 0.0
        should_warn: bool = False
        message: Optional[str] = None
        
        @property
        def expired(self) -> bool:
            return self.status == TimeoutHandler.SessionStatus.EXPIRED
        
        @property
        def inactive(self) -> bool:
            return self.status == TimeoutHandler.SessionStatus.INACTIVE
    
    def __init__(self, config: RobustnessConfig = None):
        self.config = config or RobustnessConfig()
        self._warned_sessions: Set[str] = set()
    
    def check_session(
        self,
        session_id: str,
        start_time: datetime,
        last_activity: datetime,
        current_time: datetime = None
    ) -> CheckResult:
        """
        Check session timeout status.
        
        Args:
            session_id: Session identifier
            start_time: When session started
            last_activity: Time of last activity
            current_time: Current time (defaults to now)
            
        Returns:
            CheckResult with status and timing info
        """
        current_time = current_time or datetime.now()
        
        session_age = (current_time - start_time).total_seconds()
        inactive_seconds = (current_time - last_activity).total_seconds()
        time_until_expiry = self.config.session_timeout_seconds - session_age
        
        # Check session expiration
        if session_age >= self.config.session_timeout_seconds:
            return self.CheckResult(
                status=self.SessionStatus.EXPIRED,
                inactive_seconds=inactive_seconds,
                session_age_seconds=session_age,
                time_until_expiry_seconds=0.0,
                message="Session has expired due to timeout.",
            )
        
        # Check inactivity
        if inactive_seconds >= self.config.inactivity_timeout_seconds:
            return self.CheckResult(
                status=self.SessionStatus.INACTIVE,
                inactive_seconds=inactive_seconds,
                session_age_seconds=session_age,
                time_until_expiry_seconds=time_until_expiry,
                message="Session inactive. Would you like to continue?",
            )
        
        # Warn if approaching expiry (5 minutes remaining)
        should_warn = (
            time_until_expiry < 300 and 
            session_id not in self._warned_sessions
        )
        if should_warn:
            self._warned_sessions.add(session_id)
        
        return self.CheckResult(
            status=self.SessionStatus.ACTIVE,
            inactive_seconds=inactive_seconds,
            session_age_seconds=session_age,
            time_until_expiry_seconds=time_until_expiry,
            should_warn=should_warn,
            message="Session about to expire." if should_warn else None,
        )
    
    def reset_warnings(self, session_id: str) -> None:
        """Reset warning flag for session."""
        self._warned_sessions.discard(session_id)


# =============================================================================
# IDEMPOTENT PROCESSING
# =============================================================================

@dataclass
class CachedResponse:
    """Cached response for idempotency."""
    request_hash: str
    response: Any
    timestamp: datetime
    

class IdempotencyHandler:
    """
    Request deduplication and replay protection.
    
    Uses request hashing to detect duplicate requests and return
    cached responses instead of reprocessing.
    
    Usage:
        handler = IdempotencyHandler(config)
        
        # Check if request is duplicate
        cached = handler.get_cached_response(request_data)
        if cached:
            return cached
            
        # Process request
        response = process_request(request_data)
        
        # Cache response
        handler.cache_response(request_data, response)
    """
    
    def __init__(self, config: RobustnessConfig = None):
        self.config = config or RobustnessConfig()
        self._cache: Dict[str, CachedResponse] = {}
        self._last_cleanup = datetime.now()
    
    def _compute_hash(self, request_data: Dict[str, Any]) -> str:
        """Compute deterministic hash of request data."""
        import json
        serialized = json.dumps(request_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
    
    def _cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        now = datetime.now()
        
        # Only cleanup every 10 seconds
        if (now - self._last_cleanup).total_seconds() < 10:
            return
        
        self._last_cleanup = now
        cutoff = now - timedelta(seconds=self.config.request_cache_ttl_seconds)
        
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.timestamp < cutoff
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        # Enforce max size
        if len(self._cache) > self.config.max_cached_requests:
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].timestamp
            )
            for key, _ in sorted_entries[:-self.config.max_cached_requests]:
                del self._cache[key]
    
    def get_cached_response(
        self,
        request_data: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Check for cached response.
        
        Args:
            request_data: Request parameters
            
        Returns:
            Cached response if exists and valid, None otherwise
        """
        self._cleanup_expired()
        
        request_hash = self._compute_hash(request_data)
        entry = self._cache.get(request_hash)
        
        if entry is None:
            return None
        
        # Check if expired
        age = (datetime.now() - entry.timestamp).total_seconds()
        if age > self.config.request_cache_ttl_seconds:
            del self._cache[request_hash]
            return None
        
        return entry.response
    
    def cache_response(
        self,
        request_data: Dict[str, Any],
        response: Any
    ) -> str:
        """
        Cache a response for idempotency.
        
        Args:
            request_data: Request parameters
            response: Response to cache
            
        Returns:
            Request hash
        """
        request_hash = self._compute_hash(request_data)
        
        self._cache[request_hash] = CachedResponse(
            request_hash=request_hash,
            response=response,
            timestamp=datetime.now(),
        )
        
        return request_hash
    
    def invalidate(self, request_data: Dict[str, Any]) -> bool:
        """Invalidate cached response."""
        request_hash = self._compute_hash(request_data)
        if request_hash in self._cache:
            del self._cache[request_hash]
            return True
        return False


# =============================================================================
# FSM ERROR TRANSITIONS
# =============================================================================

class FSMState(Enum):
    """FSM states with error handling."""
    GREETING = "greeting"
    EXPLORING = "exploring"
    CLARIFYING = "clarifying"
    DELIVERY = "delivery"
    FEEDBACK = "feedback"
    ENDED = "ended"
    
    # Error states
    ERROR = "error"
    TIMEOUT = "timeout"
    RECOVERY = "recovery"


@dataclass
class FSMErrorContext:
    """Context for FSM error handling."""
    error_type: str
    error_message: str
    timestamp: datetime
    previous_state: FSMState
    recovery_state: FSMState
    retry_count: int = 0


class FSMErrorHandler:
    """
    Safe FSM error handling with recovery transitions.
    
    Provides:
    - Error state transitions
    - Recovery path computation
    - Retry limiting
    
    Error Transition Rules:
    - Any state -> ERROR on exception
    - ERROR -> RECOVERY after cooldown
    - RECOVERY -> previous state or safe fallback
    - Max retries -> ENDED
    
    Usage:
        handler = FSMErrorHandler(config)
        
        try:
            # Process state
            next_state = process_state(current_state)
        except Exception as e:
            # Handle error
            transition = handler.handle_error(
                session_id,
                current_state,
                e
            )
            next_state = transition.next_state
    """
    
    # Safe fallback states for each state
    FALLBACK_STATES = {
        FSMState.GREETING: FSMState.GREETING,
        FSMState.EXPLORING: FSMState.DELIVERY,  # Fall forward to delivery
        FSMState.CLARIFYING: FSMState.DELIVERY,
        FSMState.DELIVERY: FSMState.ENDED,
        FSMState.FEEDBACK: FSMState.ENDED,
        FSMState.ERROR: FSMState.ENDED,
        FSMState.TIMEOUT: FSMState.ENDED,
        FSMState.RECOVERY: FSMState.ENDED,
    }
    
    @dataclass
    class Transition:
        """Error transition result."""
        next_state: FSMState
        should_retry: bool
        user_message: str
        log_message: str
        context: Optional[FSMErrorContext]
    
    def __init__(self, config: RobustnessConfig = None):
        self.config = config or RobustnessConfig()
        self._error_contexts: Dict[str, FSMErrorContext] = {}
        self._consecutive_errors: Dict[str, int] = {}
        self._last_error_time: Dict[str, datetime] = {}
    
    def handle_error(
        self,
        session_id: str,
        current_state: FSMState,
        error: Exception
    ) -> Transition:
        """
        Handle FSM error and compute transition.
        
        Args:
            session_id: Session identifier
            current_state: State where error occurred
            error: The exception
            
        Returns:
            Transition with next state and messages
        """
        now = datetime.now()
        
        # Track consecutive errors
        self._consecutive_errors[session_id] = self._consecutive_errors.get(session_id, 0) + 1
        consecutive = self._consecutive_errors[session_id]
        self._last_error_time[session_id] = now
        
        # Determine if we should retry
        can_retry = consecutive < self.config.max_consecutive_errors
        
        # Check cooldown
        last_error = self._last_error_time.get(session_id)
        if last_error and (now - last_error).total_seconds() < self.config.error_cooldown_seconds:
            can_retry = False
        
        # Determine next state
        if can_retry:
            next_state = FSMState.RECOVERY
        else:
            next_state = self.FALLBACK_STATES.get(current_state, FSMState.ENDED)
        
        # Create error context
        context = FSMErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=now,
            previous_state=current_state,
            recovery_state=next_state,
            retry_count=consecutive,
        )
        self._error_contexts[session_id] = context
        
        # Generate user message
        if can_retry:
            user_message = "I encountered a small issue. Let me try again..."
        elif next_state == FSMState.DELIVERY:
            user_message = "Let me make a recommendation based on what I know so far."
        else:
            user_message = "I apologize, but something went wrong. Please try starting a new conversation."
        
        return self.Transition(
            next_state=next_state,
            should_retry=can_retry,
            user_message=user_message,
            log_message=f"FSM error in {current_state}: {error}",
            context=context,
        )
    
    def resolve_recovery(
        self,
        session_id: str,
        success: bool
    ) -> FSMState:
        """
        Resolve recovery state after retry attempt.
        
        Args:
            session_id: Session identifier
            success: Whether recovery was successful
            
        Returns:
            Next state after recovery
        """
        context = self._error_contexts.get(session_id)
        
        if success:
            # Reset error counter
            self._consecutive_errors[session_id] = 0
            
            if context:
                return context.previous_state
            return FSMState.EXPLORING
        
        # Recovery failed
        if context:
            return self.FALLBACK_STATES.get(context.previous_state, FSMState.ENDED)
        return FSMState.ENDED
    
    def clear_errors(self, session_id: str) -> None:
        """Clear error tracking for session."""
        self._error_contexts.pop(session_id, None)
        self._consecutive_errors.pop(session_id, None)
        self._last_error_time.pop(session_id, None)


# =============================================================================
# COMBINED ROBUSTNESS MANAGER
# =============================================================================

class RobustnessManager:
    """
    Combined robustness manager integrating all safeguards.
    
    Provides a unified interface for all robustness features:
    - Turn limits
    - Confidence decay
    - Mood resolution
    - Timeout handling
    - Idempotency
    - Error handling
    
    Usage:
        manager = RobustnessManager()
        
        # On each turn
        status = manager.process_turn(
            session_id=session_id,
            turn_number=turn,
            confidence=confidence,
            last_activity=last_activity,
            request_data=request_data,
        )
        
        if status.requires_action:
            # Handle action (force recommendation, timeout, etc.)
    """
    
    @dataclass
    class TurnStatus:
        """Combined status for a turn."""
        allowed: bool = True
        requires_action: bool = False
        
        # Turn safeguard
        turn_warning: Optional[str] = None
        force_recommendation: bool = False
        
        # Timeout
        session_expired: bool = False
        session_inactive: bool = False
        timeout_warning: Optional[str] = None
        
        # Confidence
        decayed_confidence: float = 0.0
        
        # Idempotency
        cached_response: Optional[Any] = None
        
        # Messages
        user_messages: List[str] = field(default_factory=list)
    
    def __init__(self, config: RobustnessConfig = None):
        self.config = config or RobustnessConfig()
        
        self.turn_safeguard = TurnSafeguard(self.config)
        self.confidence_decay = ConfidenceDecay(self.config)
        self.timeout_handler = TimeoutHandler(self.config)
        self.idempotency_handler = IdempotencyHandler(self.config)
        self.fsm_error_handler = FSMErrorHandler(self.config)
        
        self._mood_resolvers: Dict[str, ContradictoryMoodResolver] = {}
    
    def process_turn(
        self,
        session_id: str,
        turn_number: int,
        confidence: float,
        session_start: datetime,
        last_activity: datetime,
        request_data: Dict[str, Any] = None,
    ) -> TurnStatus:
        """
        Process turn through all robustness checks.
        
        Args:
            session_id: Session identifier
            turn_number: Current turn number
            confidence: Current confidence score
            session_start: Session start time
            last_activity: Time of last activity
            request_data: Request data for idempotency
            
        Returns:
            TurnStatus with all check results
        """
        status = self.TurnStatus()
        messages = []
        
        # 1. Check idempotency
        if request_data:
            cached = self.idempotency_handler.get_cached_response(request_data)
            if cached:
                status.cached_response = cached
                return status
        
        # 2. Check timeout
        timeout_result = self.timeout_handler.check_session(
            session_id, session_start, last_activity
        )
        
        if timeout_result.expired:
            status.allowed = False
            status.requires_action = True
            status.session_expired = True
            messages.append(timeout_result.message)
            status.user_messages = messages
            return status
        
        if timeout_result.inactive:
            status.session_inactive = True
            status.requires_action = True
            messages.append(timeout_result.message)
        
        if timeout_result.should_warn:
            status.timeout_warning = timeout_result.message
            messages.append(timeout_result.message)
        
        # 3. Check turn limit
        turn_result = self.turn_safeguard.check_turn(session_id, turn_number)
        
        if not turn_result.allowed:
            status.allowed = False
            status.requires_action = True
            messages.append(turn_result.message)
            status.user_messages = messages
            return status
        
        if turn_result.should_force_recommendation:
            status.force_recommendation = True
            status.requires_action = True
            messages.append(turn_result.message)
        
        if turn_result.should_warn:
            status.turn_warning = turn_result.message
            messages.append(turn_result.message)
        
        # 4. Apply confidence decay
        status.decayed_confidence = self.confidence_decay.apply(
            confidence, last_activity
        )
        
        status.user_messages = messages
        return status
    
    def get_mood_resolver(self, session_id: str) -> ContradictoryMoodResolver:
        """Get or create mood resolver for session."""
        if session_id not in self._mood_resolvers:
            self._mood_resolvers[session_id] = ContradictoryMoodResolver()
        return self._mood_resolvers[session_id]
    
    def cleanup_session(self, session_id: str) -> None:
        """Clean up all session data."""
        self.turn_safeguard.reset_session(session_id)
        self.timeout_handler.reset_warnings(session_id)
        self.fsm_error_handler.clear_errors(session_id)
        self._mood_resolvers.pop(session_id, None)
    
    def cache_response(
        self,
        request_data: Dict[str, Any],
        response: Any
    ) -> str:
        """Cache response for idempotency."""
        return self.idempotency_handler.cache_response(request_data, response)


# =============================================================================
# DECORATOR FOR ROBUST FUNCTIONS
# =============================================================================

def with_robustness(
    manager: RobustnessManager = None,
    max_retries: int = 3,
    fallback_value: Any = None
):
    """
    Decorator for robust function execution.
    
    Features:
    - Automatic retry on failure
    - Fallback value on exhausted retries
    - Error logging
    
    Usage:
        @with_robustness(max_retries=3, fallback_value=[])
        def get_recommendations(user_id):
            # May fail
            return fetch_recommendations(user_id)
    """
    _manager = manager or RobustnessManager()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for "
                        f"{func.__name__}: {e}"
                    )
                    
                    # Brief delay before retry
                    if attempt < max_retries - 1:
                        time.sleep(0.5 * (attempt + 1))
            
            logger.error(
                f"All {max_retries} attempts failed for {func.__name__}: "
                f"{last_error}"
            )
            
            if fallback_value is not None:
                return fallback_value
            
            raise last_error
        
        return wrapper
    return decorator


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_robustness_manager(config: RobustnessConfig = None) -> RobustnessManager:
    """Create a RobustnessManager instance."""
    return RobustnessManager(config or RobustnessConfig())
