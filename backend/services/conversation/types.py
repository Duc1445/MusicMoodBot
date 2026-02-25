"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - TYPE DEFINITIONS
=============================================================================

Core data classes and type definitions for the Multi-Turn Conversation System.

This module contains:
- Enumerations for dialogue states, intents, and other constants
- Data classes for emotional signals, contexts, and turns
- Request/Response models for the conversation API
- Type aliases for complex types

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Union


# =============================================================================
# ENUMERATIONS
# =============================================================================

class DialogueState(Enum):
    """
    Finite State Machine states for conversation dialogue.
    
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
    """
    GREETING = auto()           # Initial state - greeting user
    PROBING_MOOD = auto()       # Asking about mood
    PROBING_INTENSITY = auto()  # Asking about intensity
    PROBING_CONTEXT = auto()    # Asking about context (activity, time, etc.)
    CONFIRMING = auto()         # Confirming understanding before recommending
    RECOMMENDING = auto()       # Generating and presenting recommendations
    FEEDBACK = auto()           # Collecting feedback on recommendations
    ENDED = auto()              # Session ended normally
    TIMEOUT = auto()            # Session timed out
    ABORTED = auto()            # User explicitly aborted


class Intent(Enum):
    """
    User intent classification categories.
    
    Used by IntentClassifier to determine user's purpose in each turn.
    """
    # Mood-related intents
    MOOD_EXPRESSION = auto()          # User expressing a mood
    MOOD_REQUEST = auto()             # User asking for mood-specific music
    MOOD_CORRECTION = auto()          # User correcting detected mood
    
    # Preference intents
    PREFERENCE_EXPRESSION = auto()    # User stating a preference
    PREFERENCE_CONSTRAINT = auto()    # User adding a constraint (not rock, etc.)
    
    # Conversation control intents
    GREETING = auto()                 # User greeting the bot
    CONFIRMATION = auto()             # User confirming something
    NEGATION = auto()                 # User denying/negating
    SKIP = auto()                     # User wants to skip questions
    HELP = auto()                     # User asking for help
    
    # Action intents
    PLAY_REQUEST = auto()             # User wants to play music
    SEARCH_REQUEST = auto()           # User searching for specific song/artist
    FEEDBACK_POSITIVE = auto()        # User gave positive feedback
    FEEDBACK_NEGATIVE = auto()        # User gave negative feedback
    
    # Context intents
    CONTEXT_EXPRESSION = auto()       # User providing context
    
    # Fallback
    UNKNOWN = auto()                  # Could not classify intent


class MoodCategory(Enum):
    """
    Primary mood categories supported by the system.
    
    Maps to the mood detection and recommendation engines.
    """
    VUI = "Vui"                  # Happy, joyful
    BUON = "Buồn"                # Sad, melancholic
    SUY_TU = "Suy tư"            # Thoughtful, reflective
    CHILL = "Chill"              # Relaxed, calm
    NANG_LUONG = "Năng lượng"    # Energetic, excited
    TAP_TRUNG = "Tập trung"      # Focused, concentrated
    
    @classmethod
    def from_string(cls, value: str) -> Optional['MoodCategory']:
        """Parse mood from string (Vietnamese or English)."""
        mappings = {
            'vui': cls.VUI, 'happy': cls.VUI, 'joyful': cls.VUI,
            'buồn': cls.BUON, 'buon': cls.BUON, 'sad': cls.BUON,
            'suy tư': cls.SUY_TU, 'suy tu': cls.SUY_TU, 'thoughtful': cls.SUY_TU,
            'chill': cls.CHILL, 'relaxed': cls.CHILL, 'calm': cls.CHILL,
            'năng lượng': cls.NANG_LUONG, 'nang luong': cls.NANG_LUONG,
            'energetic': cls.NANG_LUONG, 'energy': cls.NANG_LUONG,
            'tập trung': cls.TAP_TRUNG, 'tap trung': cls.TAP_TRUNG,
            'focused': cls.TAP_TRUNG, 'focus': cls.TAP_TRUNG,
        }
        return mappings.get(value.lower().strip())


class IntensityLevel(Enum):
    """
    Intensity levels for mood expression.
    
    Used to fine-tune music recommendations.
    """
    NHE = "Nhẹ"       # Light, subtle
    VUA = "Vừa"       # Moderate, balanced
    MANH = "Mạnh"     # Strong, intense
    
    @classmethod
    def from_string(cls, value: str) -> Optional['IntensityLevel']:
        """Parse intensity from string."""
        mappings = {
            'nhẹ': cls.NHE, 'nhe': cls.NHE, 'light': cls.NHE, 'low': cls.NHE,
            'vừa': cls.VUA, 'vua': cls.VUA, 'medium': cls.VUA, 'moderate': cls.VUA,
            'mạnh': cls.MANH, 'manh': cls.MANH, 'strong': cls.MANH, 'high': cls.MANH,
        }
        return mappings.get(value.lower().strip())


class ResponseType(Enum):
    """
    Types of bot responses in conversation.
    """
    GREETING = "greeting"                 # Initial greeting
    PROBING = "probing"                   # Asking questions
    CONFIRMATION = "confirmation"         # Confirming understanding
    RECOMMENDATION = "recommendation"     # Providing music recommendations
    CLARIFICATION = "clarification"       # Asking for clarification
    ERROR = "error"                       # Error response
    FEEDBACK_ACK = "feedback_ack"         # Acknowledging feedback


class InputType(Enum):
    """
    Types of user input.
    """
    TEXT = "text"               # Free text input
    CHIP = "chip"               # Mood chip selection
    VOICE = "voice"             # Voice input (future)
    CORRECTION = "correction"   # Explicit correction
    CONFIRMATION = "confirmation"  # Yes/No confirmation


# =============================================================================
# DATA CLASSES - EMOTIONAL SIGNALS
# =============================================================================

@dataclass
class EmotionalSignals:
    """
    Emotional signals extracted from a single user input.
    
    This captures the immediate emotional indicators from NLP processing.
    """
    # Detected mood and confidence
    mood: Optional[str] = None
    confidence: float = 0.0
    
    # Intensity detection
    intensity: Optional[str] = None
    intensity_confidence: float = 0.0
    
    # Keywords that triggered detection
    keywords_matched: List[str] = field(default_factory=list)
    
    # Negation detection (e.g., "không buồn" = not sad)
    is_negated: bool = False
    
    # Valence-Arousal estimates (optional, from deeper analysis)
    valence_estimate: Optional[float] = None   # -1.0 to 1.0
    arousal_estimate: Optional[float] = None   # 0.0 to 1.0
    
    # Explicit vs implicit mood expression
    is_explicit: bool = False  # User explicitly stated mood
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'mood': self.mood,
            'confidence': self.confidence,
            'intensity': self.intensity,
            'intensity_confidence': self.intensity_confidence,
            'keywords_matched': self.keywords_matched,
            'is_negated': self.is_negated,
            'valence_estimate': self.valence_estimate,
            'arousal_estimate': self.arousal_estimate,
            'is_explicit': self.is_explicit,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmotionalSignals':
        """Create from dictionary."""
        return cls(
            mood=data.get('mood'),
            confidence=data.get('confidence', 0.0),
            intensity=data.get('intensity'),
            intensity_confidence=data.get('intensity_confidence', 0.0),
            keywords_matched=data.get('keywords_matched', []),
            is_negated=data.get('is_negated', False),
            valence_estimate=data.get('valence_estimate'),
            arousal_estimate=data.get('arousal_estimate'),
            is_explicit=data.get('is_explicit', False),
        )


@dataclass
class MoodHistoryEntry:
    """
    A single entry in mood history tracking.
    """
    mood: str
    confidence: float
    turn_number: int
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "nlp"  # 'nlp', 'chip', 'correction'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'mood': self.mood,
            'confidence': self.confidence,
            'turn_number': self.turn_number,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MoodHistoryEntry':
        return cls(
            mood=data['mood'],
            confidence=data['confidence'],
            turn_number=data['turn_number'],
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            source=data.get('source', 'nlp'),
        )


@dataclass
class ContextSignals:
    """
    Contextual signals extracted from conversation.
    """
    # Time context
    time_of_day: Optional[str] = None    # 'morning', 'afternoon', 'evening', 'night'
    day_of_week: Optional[str] = None    # 'weekday', 'weekend'
    
    # Activity context
    activity: Optional[str] = None       # 'working', 'relaxing', 'exercising', 'commuting'
    
    # Social context
    social: Optional[str] = None         # 'alone', 'with_friends', 'party'
    
    # Location context (if provided)
    location: Optional[str] = None       # 'home', 'office', 'gym', 'car'
    
    # User preferences mentioned
    genre_preferences: List[str] = field(default_factory=list)
    artist_preferences: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)  # e.g., 'no rock'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'time_of_day': self.time_of_day,
            'day_of_week': self.day_of_week,
            'activity': self.activity,
            'social': self.social,
            'location': self.location,
            'genre_preferences': self.genre_preferences,
            'artist_preferences': self.artist_preferences,
            'constraints': self.constraints,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextSignals':
        return cls(
            time_of_day=data.get('time_of_day'),
            day_of_week=data.get('day_of_week'),
            activity=data.get('activity'),
            social=data.get('social'),
            location=data.get('location'),
            genre_preferences=data.get('genre_preferences', []),
            artist_preferences=data.get('artist_preferences', []),
            constraints=data.get('constraints', []),
        )


@dataclass
class EmotionalContext:
    """
    Accumulated emotional context across a conversation session.
    
    This represents the aggregated understanding of the user's emotional state
    built up over multiple turns of conversation.
    """
    # Primary detected mood
    primary_mood: Optional[str] = None
    primary_intensity: Optional[str] = None
    mood_confidence: float = 0.0
    
    # History tracking
    mood_history: List[MoodHistoryEntry] = field(default_factory=list)
    
    # VA space estimates
    valence_estimate: float = 0.0      # -1.0 to 1.0
    arousal_estimate: float = 0.5      # 0.0 to 1.0
    
    # Context factors
    context: ContextSignals = field(default_factory=ContextSignals)
    
    # Clarity components
    mood_specified: bool = False
    intensity_specified: bool = False
    context_richness: float = 0.0      # 0.0 to 1.0
    consistency_score: float = 1.0     # 0.0 to 1.0
    
    # All keywords collected
    all_keywords: List[str] = field(default_factory=list)
    
    # Clarification state
    requires_clarification: bool = True
    clarification_attempts: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_mood_observation(self, mood: str, confidence: float, 
                             turn_number: int, source: str = 'nlp'):
        """Add a mood observation to history."""
        entry = MoodHistoryEntry(
            mood=mood,
            confidence=confidence,
            turn_number=turn_number,
            source=source,
        )
        self.mood_history.append(entry)
        self.updated_at = datetime.now()
        
        # Update primary if higher confidence
        if confidence > self.mood_confidence:
            self.primary_mood = mood
            self.mood_confidence = confidence
            self.mood_specified = True
        
        # Update consistency score
        self._update_consistency()
    
    def _update_consistency(self):
        """Update mood consistency score based on history."""
        if len(self.mood_history) < 2:
            self.consistency_score = 1.0
            return
        
        # Count mood changes
        mood_changes = 0
        for i in range(1, len(self.mood_history)):
            if self.mood_history[i].mood != self.mood_history[i-1].mood:
                mood_changes += 1
        
        # Higher changes = lower consistency
        self.consistency_score = max(0.0, 1.0 - (mood_changes / len(self.mood_history)))
    
    def merge_context(self, new_context: ContextSignals):
        """Merge new context signals into accumulated context."""
        if new_context.time_of_day:
            self.context.time_of_day = new_context.time_of_day
        if new_context.day_of_week:
            self.context.day_of_week = new_context.day_of_week
        if new_context.activity:
            self.context.activity = new_context.activity
        if new_context.social:
            self.context.social = new_context.social
        if new_context.location:
            self.context.location = new_context.location
        
        self.context.genre_preferences.extend(new_context.genre_preferences)
        self.context.artist_preferences.extend(new_context.artist_preferences)
        self.context.constraints.extend(new_context.constraints)
        
        # Remove duplicates
        self.context.genre_preferences = list(set(self.context.genre_preferences))
        self.context.artist_preferences = list(set(self.context.artist_preferences))
        self.context.constraints = list(set(self.context.constraints))
        
        # Update context richness
        self._update_context_richness()
        self.updated_at = datetime.now()
    
    def _update_context_richness(self):
        """Calculate context richness score."""
        factors = [
            self.context.time_of_day is not None,
            self.context.activity is not None,
            self.context.social is not None,
            len(self.context.genre_preferences) > 0,
            len(self.context.artist_preferences) > 0,
        ]
        self.context_richness = sum(factors) / len(factors)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'primary_mood': self.primary_mood,
            'primary_intensity': self.primary_intensity,
            'mood_confidence': self.mood_confidence,
            'mood_history': [e.to_dict() for e in self.mood_history],
            'valence_estimate': self.valence_estimate,
            'arousal_estimate': self.arousal_estimate,
            'context': self.context.to_dict(),
            'mood_specified': self.mood_specified,
            'intensity_specified': self.intensity_specified,
            'context_richness': self.context_richness,
            'consistency_score': self.consistency_score,
            'all_keywords': self.all_keywords,
            'requires_clarification': self.requires_clarification,
            'clarification_attempts': self.clarification_attempts,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmotionalContext':
        """Create from dictionary."""
        ctx = cls(
            primary_mood=data.get('primary_mood'),
            primary_intensity=data.get('primary_intensity'),
            mood_confidence=data.get('mood_confidence', 0.0),
            mood_history=[MoodHistoryEntry.from_dict(e) for e in data.get('mood_history', [])],
            valence_estimate=data.get('valence_estimate', 0.0),
            arousal_estimate=data.get('arousal_estimate', 0.5),
            mood_specified=data.get('mood_specified', False),
            intensity_specified=data.get('intensity_specified', False),
            context_richness=data.get('context_richness', 0.0),
            consistency_score=data.get('consistency_score', 1.0),
            all_keywords=data.get('all_keywords', []),
            requires_clarification=data.get('requires_clarification', True),
            clarification_attempts=data.get('clarification_attempts', 0),
        )
        
        if 'context' in data:
            ctx.context = ContextSignals.from_dict(data['context'])
        
        if 'created_at' in data:
            ctx.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            ctx.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return ctx


# =============================================================================
# DATA CLASSES - CONVERSATION TURNS
# =============================================================================

@dataclass
class ConversationTurn:
    """
    A single turn in the conversation.
    
    Represents one user input + one bot response cycle.
    """
    # Identification
    turn_id: Optional[int] = None
    session_id: str = ""
    turn_number: int = 0
    
    # User input
    user_input: str = ""
    input_type: InputType = InputType.TEXT
    
    # NLP detection results
    detected_mood: Optional[str] = None
    detected_intensity: Optional[str] = None
    mood_confidence: float = 0.0
    keywords_matched: List[str] = field(default_factory=list)
    
    # Intent classification
    intent: Optional[Intent] = None
    intent_confidence: float = 0.0
    
    # Signals
    emotional_signals: Optional[EmotionalSignals] = None
    context_signals: Optional[ContextSignals] = None
    
    # Bot response
    bot_response: str = ""
    response_type: ResponseType = ResponseType.PROBING
    question_asked: Optional[str] = None  # Question ID if probing
    
    # State tracking
    state_before: DialogueState = DialogueState.GREETING
    state_after: DialogueState = DialogueState.GREETING
    
    # Clarity metrics
    clarity_score_before: float = 0.0
    clarity_score_after: float = 0.0
    clarity_delta: float = 0.0
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/DB serialization."""
        return {
            'turn_id': self.turn_id,
            'session_id': self.session_id,
            'turn_number': self.turn_number,
            'user_input': self.user_input,
            'input_type': self.input_type.value if self.input_type else 'text',
            'detected_mood': self.detected_mood,
            'detected_intensity': self.detected_intensity,
            'mood_confidence': self.mood_confidence,
            'keywords_matched': self.keywords_matched,
            'intent': self.intent.name if self.intent else None,
            'intent_confidence': self.intent_confidence,
            'emotional_signals': self.emotional_signals.to_dict() if self.emotional_signals else None,
            'context_signals': self.context_signals.to_dict() if self.context_signals else None,
            'bot_response': self.bot_response,
            'response_type': self.response_type.value if self.response_type else 'probing',
            'question_asked': self.question_asked,
            'state_before': self.state_before.name if self.state_before else 'GREETING',
            'state_after': self.state_after.name if self.state_after else 'GREETING',
            'clarity_score_before': self.clarity_score_before,
            'clarity_score_after': self.clarity_score_after,
            'clarity_delta': self.clarity_delta,
            'created_at': self.created_at.isoformat(),
            'processing_time_ms': self.processing_time_ms,
        }


@dataclass
class ConversationSession:
    """
    A conversation session spanning multiple turns.
    """
    # Identification
    session_id: str = ""
    user_id: int = 0
    
    # State
    state: DialogueState = DialogueState.GREETING
    
    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    last_activity_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Turn tracking
    turn_count: int = 0
    max_turns: int = 5
    turns: List[ConversationTurn] = field(default_factory=list)
    
    # Final results
    final_mood: Optional[str] = None
    final_intensity: Optional[str] = None
    final_confidence: float = 0.0
    
    # Emotional context
    emotional_context: EmotionalContext = field(default_factory=EmotionalContext)
    
    # Session flags
    is_active: bool = True
    early_exit_reason: Optional[str] = None
    
    # Client metadata
    client_info: Dict[str, Any] = field(default_factory=dict)
    
    def add_turn(self, turn: ConversationTurn):
        """Add a turn to the session."""
        turn.session_id = self.session_id
        turn.turn_number = len(self.turns)
        self.turns.append(turn)
        self.turn_count = len(self.turns)
        self.last_activity_at = datetime.now()
        self.state = turn.state_after
    
    def end_session(self, reason: Optional[str] = None):
        """End the session."""
        self.is_active = False
        self.ended_at = datetime.now()
        self.state = DialogueState.ENDED
        self.early_exit_reason = reason
        
        # Finalize mood from emotional context
        if self.emotional_context.primary_mood:
            self.final_mood = self.emotional_context.primary_mood
            self.final_intensity = self.emotional_context.primary_intensity
            self.final_confidence = self.emotional_context.mood_confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/DB serialization."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'state': self.state.name if self.state else 'GREETING',
            'started_at': self.started_at.isoformat(),
            'last_activity_at': self.last_activity_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'turn_count': self.turn_count,
            'max_turns': self.max_turns,
            'final_mood': self.final_mood,
            'final_intensity': self.final_intensity,
            'final_confidence': self.final_confidence,
            'emotional_context': self.emotional_context.to_dict(),
            'is_active': self.is_active,
            'early_exit_reason': self.early_exit_reason,
            'client_info': self.client_info,
        }


# =============================================================================
# DATA CLASSES - REQUESTS AND RESPONSES
# =============================================================================

@dataclass
class TurnRequest:
    """
    Request to process a conversation turn.
    """
    session_id: str
    user_input: str
    input_type: InputType = InputType.TEXT
    
    # Optional metadata
    client_timestamp: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'user_input': self.user_input,
            'input_type': self.input_type.value,
            'client_timestamp': self.client_timestamp.isoformat() if self.client_timestamp else None,
            'idempotency_key': self.idempotency_key,
        }


@dataclass
class TurnResponse:
    """
    Response from processing a conversation turn.
    """
    # Success flag
    success: bool = True
    
    # Session info
    session_id: str = ""
    turn_number: int = 0
    state: DialogueState = DialogueState.GREETING
    
    # Bot response
    bot_message: str = ""
    response_type: ResponseType = ResponseType.PROBING
    
    # Detected information
    detected_mood: Optional[str] = None
    detected_intensity: Optional[str] = None
    mood_confidence: float = 0.0
    
    # Clarity score
    clarity_score: float = 0.0
    
    # Control flags
    require_input: bool = True          # Expect more user input
    can_recommend: bool = False         # Ready to recommend
    show_mood_chips: bool = False       # Show mood selection chips
    
    # Recommendations (if state == RECOMMENDING)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    playlist_id: Optional[int] = None
    
    # Error info
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'session_id': self.session_id,
            'turn_number': self.turn_number,
            'state': self.state.name if self.state else 'GREETING',
            'bot_message': self.bot_message,
            'response_type': self.response_type.value if self.response_type else 'probing',
            'detected_mood': self.detected_mood,
            'detected_intensity': self.detected_intensity,
            'mood_confidence': self.mood_confidence,
            'clarity_score': self.clarity_score,
            'require_input': self.require_input,
            'can_recommend': self.can_recommend,
            'show_mood_chips': self.show_mood_chips,
            'recommendations': self.recommendations,
            'playlist_id': self.playlist_id,
            'error': self.error,
        }


@dataclass
class SessionStartRequest:
    """
    Request to start a new conversation session.
    """
    user_id: int
    initial_message: Optional[str] = None
    client_info: Dict[str, Any] = field(default_factory=dict)
    max_turns: int = 5


@dataclass
class SessionStartResponse:
    """
    Response from starting a conversation session.
    """
    success: bool = True
    session_id: str = ""
    greeting_message: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'session_id': self.session_id,
            'greeting_message': self.greeting_message,
            'error': self.error,
        }


@dataclass
class EnrichedRequest:
    """
    Enriched request for ChatOrchestrator after conversation processing.
    
    Contains all accumulated context and clarity for recommendation generation.
    """
    # User identification
    user_id: int
    session_id: str
    
    # Final mood determination
    mood: str
    mood_vi: str
    intensity: str
    confidence: float
    
    # Source of determination
    source: str = "conversation"  # 'conversation', 'single_turn', 'chip'
    
    # Full emotional context
    emotional_context: EmotionalContext = field(default_factory=EmotionalContext)
    
    # Preferences extracted from conversation
    genre_preferences: List[str] = field(default_factory=list)
    artist_preferences: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    # Activity context
    activity: Optional[str] = None
    time_context: Optional[str] = None
    
    # Request parameters
    limit: int = 10
    exclude_song_ids: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'mood': self.mood,
            'mood_vi': self.mood_vi,
            'intensity': self.intensity,
            'confidence': self.confidence,
            'source': self.source,
            'emotional_context': self.emotional_context.to_dict(),
            'genre_preferences': self.genre_preferences,
            'artist_preferences': self.artist_preferences,
            'constraints': self.constraints,
            'activity': self.activity,
            'time_context': self.time_context,
            'limit': self.limit,
            'exclude_song_ids': self.exclude_song_ids,
        }


# =============================================================================
# TYPE ALIASES
# =============================================================================

# Clarity score tuple: (score, components_dict)
ClarityResult = Tuple[float, Dict[str, float]]

# Transition guard function signature
TransitionGuard = callable  # (session: ConversationSession) -> bool

# State transition entry: (target_state, guard, priority)
TransitionEntry = Tuple[DialogueState, Optional[TransitionGuard], int]

# JSON-serializable dict
JSONDict = Dict[str, Any]


# =============================================================================
# CONSTANTS
# =============================================================================

# Maximum turns before forcing recommendation
MAX_TURNS_DEFAULT = 5
MAX_TURNS_PER_SESSION = 5  # Alias for consistency

# Clarity threshold for confident recommendation
CLARITY_THRESHOLD_HIGH = 0.8
CLARITY_THRESHOLD_MEDIUM = 0.6
CLARITY_THRESHOLD_LOW = 0.4
CLARITY_THRESHOLD = 0.6  # Default threshold (medium)

# Minimum confidence threshold for mood detection
MIN_CONFIDENCE_THRESHOLD = 0.5

# Session timeout in seconds (30 minutes)
SESSION_TIMEOUT_SECONDS = 1800

# Idempotency key expiry in seconds (5 minutes)
IDEMPOTENCY_KEY_EXPIRY_SECONDS = 300
