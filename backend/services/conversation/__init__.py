"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM
=============================================================================

A sophisticated multi-turn conversation system for MusicMoodBot.

This package provides:
- FSM-based dialogue management
- Emotional depth tracking with accumulation
- Clarity scoring for mood understanding
- Intent classification
- Probing question selection
- Session persistence
- Context signal extraction

Architecture Overview:
    
    +------------------+
    |  API Layer       |  <-- TurnRequest
    +------------------+
            |
            v
    +------------------+
    | ConversationMgr  |  <-- Main orchestrator
    +------------------+
            |
            v
    +------------------+
    | IntentClassifier |  --> Detects user intent
    +------------------+
            |
            v
    +------------------+
    | EmotionTracker   |  --> Accumulates mood signals
    +------------------+
            |
            v
    +------------------+
    | ClarityModel     |  --> Scores understanding
    +------------------+
            |
            v
    +------------------+
    | DialogueFSM      |  --> State transitions
    +------------------+
            |
            v
    +------------------+
    | StrategyEngine   |  --> Determines approach
    +------------------+
            |
            v
    +------------------+
    | QuestionBank     |  --> Selects questions
    +------------------+
            |
            v
    +------------------+
    | Response Gen     |  --> Bot response
    +------------------+
            |
            v
    +------------------+
    | SessionStore     |  --> Persist to DB
    +------------------+

Usage:
    from backend.services.conversation import ConversationManager
    
    # Create manager
    manager = ConversationManager()
    
    # Process user turn
    response = manager.process_turn(
        user_id=123,
        input_text="Hôm nay tôi buồn quá",
        session_id=None
    )
    
    # Check if ready for recommendation
    if response.should_recommend:
        enriched = manager.get_enriched_request(response.session_id)
        # Pass to recommendation pipeline

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

# Core types
from .types import (
    # Enums
    DialogueState,
    Intent,
    InputType,
    ResponseType,
    
    # Data classes
    EmotionalSignals,
    ContextSignals,
    EmotionalContext,
    ConversationTurn,
    ConversationSession,
    TurnRequest,
    TurnResponse,
    EnrichedRequest,
    
    # Constants
    SESSION_TIMEOUT_SECONDS,
    MAX_TURNS_PER_SESSION,
    CLARITY_THRESHOLD,
    MIN_CONFIDENCE_THRESHOLD,
    IDEMPOTENCY_KEY_EXPIRY_SECONDS,
)

# State machine
from .state_machine import (
    DialogueFSM,
    Transition,
)

# Emotion tracking
from .emotion_tracker import (
    EmotionDepthTracker,
)

# Clarity scoring
from .clarity_scorer import (
    EmotionClarityModel,
    ClarityWeights,
)

# Intent classification
from .intent_classifier import (
    IntentClassifier,
)

# Strategy engine
from .strategy_engine import (
    ClarificationStrategy,
    ClarificationStrategyEngine,
)

# Question bank
from .question_bank import (
    ProbingQuestion,
    ProbeQuestionBank,
)

# Session store
from .session_store import (
    SessionStore,
    create_session_store,
)

# Context extraction
from .context_extractor import (
    ContextSignalExtractor,
    create_context_extractor,
)

# Main manager
from .manager import (
    ConversationManager,
    create_conversation_manager,
)

# v5.0 Context Memory
from .conversation_context import (
    ConversationTurn as ConversationTurnV5,
    ConversationContextMemory,
    ConversationContextStore,
    get_context_store,
)

# v5.0 Emotional Trajectory
from .emotional_trajectory import (
    VAPoint,
    EmotionalTrend,
    EmotionalTrajectoryTracker,
    get_trajectory_tracker,
    mood_to_va,
    va_to_mood,
)

# v5.0 Session Rewards
from .session_reward import (
    FeedbackType,
    RewardEvent,
    SessionRewardCalculator,
    SessionRewardStore,
    get_reward_store,
)

# Version
__version__ = '5.0.0'

# Public API
__all__ = [
    # Manager (main entry point)
    'ConversationManager',
    'create_conversation_manager',
    
    # Enums
    'DialogueState',
    'Intent',
    'InputType',
    'ResponseType',
    'ClarificationStrategy',
    
    # Data classes
    'EmotionalSignals',
    'ContextSignals',
    'EmotionalContext',
    'ConversationTurn',
    'ConversationSession',
    'TurnRequest',
    'TurnResponse',
    'EnrichedRequest',
    'ProbingQuestion',
    
    # Components
    'DialogueFSM',
    'Transition',
    'EmotionDepthTracker',
    'EmotionClarityModel',
    'ClarityWeights',
    'IntentClassifier',
    'ClarificationStrategyEngine',
    'ProbeQuestionBank',
    'SessionStore',
    'ContextSignalExtractor',
    
    # Factory functions
    'create_session_store',
    'create_context_extractor',
    
    # Constants
    'SESSION_TIMEOUT_SECONDS',
    'MAX_TURNS_PER_SESSION',
    'CLARITY_THRESHOLD',
    'MIN_CONFIDENCE_THRESHOLD',
    'IDEMPOTENCY_KEY_EXPIRY_SECONDS',
    
    # v5.0 Context Memory
    'ConversationTurnV5',
    'ConversationContextMemory',
    'ConversationContextStore',
    'get_context_store',
    
    # v5.0 Emotional Trajectory
    'VAPoint',
    'EmotionalTrend',
    'EmotionalTrajectoryTracker',
    'get_trajectory_tracker',
    'mood_to_va',
    'va_to_mood',
    
    # v5.0 Session Rewards
    'FeedbackType',
    'RewardEvent',
    'SessionRewardCalculator',
    'SessionRewardStore',
    'get_reward_store',
    
    # Version
    '__version__',
]
