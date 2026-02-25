"""
=============================================================================
MULTI-TURN CONVERSATION API ROUTER
=============================================================================

Endpoints for multi-turn conversation-based music recommendations.

This API provides:
- POST /conversation/turn - Process a conversation turn
- POST /conversation/start - Start a new conversation
- GET /conversation/session/{session_id} - Get session status
- POST /conversation/end/{session_id} - End a conversation
- GET /conversation/recommend/{session_id} - Get recommendations from session

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.services.conversation import (
    ConversationManager,
    create_conversation_manager,
    TurnResponse,
    EnrichedRequest,
    InputType,
    DialogueState,
)
from backend.api.v1.dependencies import get_current_user_id

router = APIRouter()


# =============================================================================
# GLOBAL MANAGER INSTANCE
# =============================================================================

_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get or create the ConversationManager singleton."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = create_conversation_manager()
    return _conversation_manager


def set_conversation_manager(manager: ConversationManager):
    """Set the ConversationManager instance (for testing)."""
    global _conversation_manager
    _conversation_manager = manager


# =============================================================================
# REQUEST MODELS
# =============================================================================

class ConversationTurnRequest(BaseModel):
    """Request body for processing a conversation turn."""
    message: str = Field(..., description="User's message text", min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="Existing session ID (optional)")
    input_type: str = Field("text", description="Input type: 'text', 'emoji', 'tap', 'chip'")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Client metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hôm nay tôi cảm thấy buồn quá",
                "input_type": "text"
            }
        }


class StartConversationRequest(BaseModel):
    """Request body for starting a new conversation."""
    greeting_message: Optional[str] = Field(None, description="Optional initial greeting")
    client_info: Optional[Dict[str, Any]] = Field(None, description="Client metadata")
    language: str = Field("vi", description="Preferred language: 'vi' or 'en'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "vi",
                "client_info": {"device": "mobile", "platform": "android"}
            }
        }


class EndConversationRequest(BaseModel):
    """Request body for ending a conversation."""
    reason: str = Field("user_exit", description="Reason for ending")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "user_exit"
            }
        }


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class ConversationTurnResponse(BaseModel):
    """Response for a conversation turn."""
    session_id: str
    turn_number: int
    bot_response: str
    response_type: str
    detected_mood: Optional[str] = None
    detected_intensity: Optional[float] = None
    clarity_score: float = 0.0
    current_state: str
    should_recommend: bool = False
    session_ended: bool = False
    processing_time_ms: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123-def",
                "turn_number": 1,
                "bot_response": "Mình hiểu. Bạn đang buồn vì chuyện gì vậy?",
                "response_type": "probing",
                "detected_mood": "sad",
                "detected_intensity": 0.7,
                "clarity_score": 0.45,
                "current_state": "PROBING_DEPTH",
                "should_recommend": False,
                "processing_time_ms": 120
            }
        }


class SessionStatusResponse(BaseModel):
    """Response for session status."""
    session_id: str
    user_id: int
    turn_count: int
    current_state: str
    final_mood: Optional[str] = None
    final_intensity: Optional[float] = None
    clarity_score: float = 0.0
    is_active: bool = True
    started_at: str
    last_activity: str
    should_recommend: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123-def",
                "user_id": 1,
                "turn_count": 3,
                "current_state": "CONFIRMING_MOOD",
                "final_mood": "sad",
                "final_intensity": 0.7,
                "clarity_score": 0.82,
                "is_active": True,
                "started_at": "2024-01-15T10:30:00",
                "last_activity": "2024-01-15T10:32:00",
                "should_recommend": True
            }
        }


class EnrichedRequestResponse(BaseModel):
    """Response containing enriched request data for recommendations."""
    session_id: str
    user_id: int
    final_mood: Optional[str] = None
    final_intensity: float = 0.5
    clarity_score: float = 0.0
    valence: float = 0.0
    arousal: float = 0.5
    mood_history: List[str] = []
    context: Dict[str, Any] = {}
    ready_for_recommendation: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123-def",
                "user_id": 1,
                "final_mood": "sad",
                "final_intensity": 0.7,
                "clarity_score": 0.85,
                "valence": -0.6,
                "arousal": 0.3,
                "mood_history": ["anxious", "sad", "sad"],
                "context": {
                    "activity": "relaxing",
                    "time_of_day": "evening"
                },
                "ready_for_recommendation": True
            }
        }


# =============================================================================
# CONVERSATION ENDPOINTS
# =============================================================================

@router.post("/turn", response_model=ConversationTurnResponse)
async def process_turn(
    request: ConversationTurnRequest,
    user_id: int = Depends(get_current_user_id)
) -> ConversationTurnResponse:
    """
    Process a conversation turn.
    
    This is the main endpoint for multi-turn conversations.
    
    - Accepts user message
    - Detects mood and intent
    - Updates conversation state
    - Returns bot response with probing questions or recommendations
    
    The system automatically:
    - Creates a new session if session_id is not provided
    - Tracks emotional signals across turns
    - Calculates clarity score
    - Determines when enough information is gathered
    """
    manager = get_conversation_manager()
    
    # Map input type
    input_type_map = {
        'text': InputType.TEXT,
        'emoji': InputType.EMOJI,
        'tap': InputType.TAP,
        'chip': InputType.CHIP,
    }
    input_type = input_type_map.get(request.input_type, InputType.TEXT)
    
    # Process turn
    try:
        response = manager.process_turn(
            user_id=user_id,
            input_text=request.message,
            session_id=request.session_id,
            input_type=input_type,
            client_info=request.client_info
        )
        
        return ConversationTurnResponse(
            session_id=response.session_id,
            turn_number=response.turn_number,
            bot_response=response.bot_response,
            response_type=response.response_type.value if response.response_type else 'unknown',
            detected_mood=response.detected_mood,
            detected_intensity=response.detected_intensity,
            clarity_score=response.clarity_score,
            current_state=response.current_state,
            should_recommend=response.should_recommend,
            session_ended=response.session_ended,
            processing_time_ms=response.processing_time_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing turn: {str(e)}")


@router.post("/start", response_model=ConversationTurnResponse)
async def start_conversation(
    request: StartConversationRequest,
    user_id: int = Depends(get_current_user_id)
) -> ConversationTurnResponse:
    """
    Start a new conversation session.
    
    Creates a fresh session and returns the greeting.
    
    Use this when:
    - User explicitly wants to start over
    - Beginning a new recommendation flow
    """
    manager = get_conversation_manager()
    
    # Set language preference
    if request.language in ('vi', 'en'):
        manager.language = request.language
    
    # If there's a greeting message, process it as first turn
    if request.greeting_message:
        response = manager.process_turn(
            user_id=user_id,
            input_text=request.greeting_message,
            session_id=None,  # Force new session
            input_type=InputType.TEXT,
            client_info=request.client_info
        )
    else:
        # Create session and return greeting
        session = manager._get_or_create_session(
            user_id=user_id,
            session_id=None,
            client_info=request.client_info
        )
        import random
        from backend.services.conversation.manager import GREETING_RESPONSES
        lang = request.language
        greeting = random.choice(GREETING_RESPONSES.get(lang, GREETING_RESPONSES['vi']))
        
        response = TurnResponse(
            session_id=session.session_id,
            turn_number=0,
            bot_response=greeting,
            response_type='greeting',
            current_state='GREETING',
            should_recommend=False,
        )
    
    return ConversationTurnResponse(
        session_id=response.session_id,
        turn_number=response.turn_number,
        bot_response=response.bot_response,
        response_type=response.response_type.value if hasattr(response.response_type, 'value') else str(response.response_type),
        detected_mood=response.detected_mood,
        detected_intensity=response.detected_intensity,
        clarity_score=response.clarity_score,
        current_state=response.current_state,
        should_recommend=response.should_recommend,
        session_ended=response.session_ended if hasattr(response, 'session_ended') else False,
        processing_time_ms=response.processing_time_ms if hasattr(response, 'processing_time_ms') else 0,
    )


@router.get("/session/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str = Path(..., description="Session ID"),
    user_id: int = Depends(get_current_user_id)
) -> SessionStatusResponse:
    """
    Get the status of a conversation session.
    
    Returns:
    - Current state
    - Turn count
    - Detected mood/intensity
    - Clarity score
    - Whether recommendations are ready
    """
    manager = get_conversation_manager()
    summary = manager.get_session_summary(session_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify user owns this session
    if summary['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Determine if ready for recommendation
    should_recommend = summary['state'] in ('RECOMMENDATION', 'DELIVERY', 'CONFIRMING_MOOD')
    
    return SessionStatusResponse(
        session_id=summary['session_id'],
        user_id=summary['user_id'],
        turn_count=summary['turn_count'],
        current_state=summary['state'],
        final_mood=summary['final_mood'],
        final_intensity=summary['final_intensity'],
        clarity_score=summary['clarity_score'],
        is_active=summary['is_active'],
        started_at=summary['started_at'] or '',
        last_activity=summary.get('last_activity', summary['started_at'] or ''),
        should_recommend=should_recommend,
    )


@router.post("/end/{session_id}")
async def end_conversation(
    session_id: str = Path(..., description="Session ID"),
    request: EndConversationRequest = EndConversationRequest(),
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    End a conversation session.
    
    Marks the session as inactive and records the end reason.
    """
    manager = get_conversation_manager()
    
    # Verify session exists and user owns it
    summary = manager.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    if summary['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # End session
    manager.end_session(session_id, reason=request.reason)
    
    return {
        "success": True,
        "session_id": session_id,
        "reason": request.reason,
        "final_mood": summary['final_mood'],
        "final_intensity": summary['final_intensity'],
        "turn_count": summary['turn_count'],
    }


@router.get("/recommend/{session_id}", response_model=EnrichedRequestResponse)
async def get_recommendation_data(
    session_id: str = Path(..., description="Session ID"),
    user_id: int = Depends(get_current_user_id)
) -> EnrichedRequestResponse:
    """
    Get enriched request data for recommendations.
    
    Returns accumulated emotional context from the conversation,
    ready to be passed to the recommendation pipeline.
    
    Use this after should_recommend=True in turn response.
    """
    manager = get_conversation_manager()
    
    # Verify session
    summary = manager.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    if summary['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get enriched request
    enriched = manager.get_enriched_request(session_id)
    if not enriched:
        raise HTTPException(status_code=404, detail="No enriched data available")
    
    # Determine if ready
    ready = (
        enriched.clarity_score >= 0.75 and
        enriched.final_mood is not None
    )
    
    # Build context
    context = {}
    if enriched.context_signals:
        context = {
            'activity': enriched.context_signals.activity,
            'time_of_day': enriched.context_signals.time_of_day,
            'location': enriched.context_signals.location,
            'social_context': enriched.context_signals.social_context,
        }
    
    return EnrichedRequestResponse(
        session_id=enriched.session_id,
        user_id=enriched.user_id,
        final_mood=enriched.final_mood,
        final_intensity=enriched.final_intensity,
        clarity_score=enriched.clarity_score,
        valence=enriched.valence,
        arousal=enriched.arousal,
        mood_history=enriched.mood_history,
        context=context,
        ready_for_recommendation=ready,
    )


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.post("/cleanup")
async def cleanup_expired_sessions() -> Dict[str, Any]:
    """
    Clean up expired sessions.
    
    Admin endpoint for maintenance.
    """
    manager = get_conversation_manager()
    count = manager.cleanup_expired_sessions()
    
    return {
        "success": True,
        "sessions_cleaned": count,
    }


@router.get("/health")
async def conversation_health() -> Dict[str, Any]:
    """Health check for conversation system."""
    manager = get_conversation_manager()
    
    return {
        "status": "healthy",
        "version": "3.0.0",
        "components": {
            "session_store": "ok",
            "fsm": "ok",
            "emotion_tracker": "ok",
            "clarity_model": "ok",
            "intent_classifier": "ok",
            "question_bank": "ok",
            "context_extractor": "ok",
        },
    }
