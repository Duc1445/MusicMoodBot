"""
Chat API Router
===============
Endpoints for chat-based music recommendations.

Endpoints:
- POST /chat/message - Send message and get recommendations
- POST /chat/feedback - Submit feedback on a song
- GET /chat/session/{session_id} - Get session history
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.services import (
    get_chat_orchestrator,
    ChatResponse as OrchestratorResponse,
    SongRecommendation
)
from backend.api.v1.dependencies import get_current_user_id

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ChatMessageRequest(BaseModel):
    """Request body for chat message."""
    message: Optional[str] = Field(None, description="Text message for NLP mood detection")
    mood: Optional[str] = Field(None, description="Direct mood selection (Vui, Buồn, etc.)")
    intensity: Optional[str] = Field(None, description="Intensity level (Nhẹ, Vừa, Mạnh)")
    input_type: str = Field("text", description="'text' for NLP, 'chip' for direct selection")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    limit: int = Field(10, ge=1, le=20, description="Maximum songs to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Tôi đang cảm thấy buồn và cô đơn",
                "input_type": "text",
                "limit": 10
            }
        }


class ChatChipRequest(BaseModel):
    """Request body for chip-based mood selection."""
    mood: str = Field(..., description="Mood (Vui, Buồn, Suy tư, Chill, Năng lượng)")
    intensity: str = Field("Vừa", description="Intensity (Nhẹ, Vừa, Mạnh)")
    session_id: Optional[str] = None
    limit: int = Field(10, ge=1, le=20)
    
    class Config:
        json_schema_extra = {
            "example": {
                "mood": "Vui",
                "intensity": "Vừa",
                "limit": 10
            }
        }


class FeedbackRequest(BaseModel):
    """Request body for song feedback."""
    song_id: int = Field(..., description="ID of the song")
    feedback_type: str = Field(..., description="'like', 'dislike', or 'skip'")
    history_id: Optional[int] = Field(None, description="Optional history entry ID")
    listened_duration_seconds: Optional[int] = Field(None, description="Seconds listened")
    
    class Config:
        json_schema_extra = {
            "example": {
                "song_id": 42,
                "feedback_type": "like",
                "listened_duration_seconds": 180
            }
        }


class SongResponse(BaseModel):
    """Response model for a song."""
    song_id: int
    name: str
    artist: str
    genre: str
    mood: str
    reason: str
    match_score: float
    audio_features: Dict[str, float]


class MoodDetectionResponse(BaseModel):
    """Response model for mood detection result."""
    mood: str
    mood_vi: str
    confidence: float
    intensity: str
    keywords_matched: List[str]


class ChatMessageResponse(BaseModel):
    """Response body for chat message."""
    status: str
    detected_mood: Optional[MoodDetectionResponse]
    bot_message: str
    songs: List[SongResponse]
    playlist_id: Optional[int]
    session_id: str
    require_mood_selection: bool = False


class FeedbackResponse(BaseModel):
    """Response body for feedback."""
    status: str
    message: str
    preference_updated: bool


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Send a chat message and receive song recommendations.
    
    **Text Input (NLP):**
    - Send natural language text describing your mood
    - System detects mood using NLP and returns matching songs
    
    **Chip Input (Direct):**
    - Set `input_type` to "chip"
    - Provide `mood` and `intensity` directly
    
    **Pipeline:**
    1. Mood Detection (NLP or direct)
    2. Candidate Selection (MoodEngine)
    3. Personalization (PreferenceModel)
    4. Playlist Curation (CuratorEngine)
    """
    orchestrator = get_chat_orchestrator()
    
    result = orchestrator.process_message(
        user_id=user_id,
        message=request.message,
        mood=request.mood,
        intensity=request.intensity,
        input_type=request.input_type,
        session_id=request.session_id,
        limit=request.limit
    )
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    # Convert to response format
    songs = []
    for s in result.songs:
        songs.append(SongResponse(
            song_id=s.song_id,
            name=s.name,
            artist=s.artist,
            genre=s.genre,
            mood=s.mood,
            reason=s.reason,
            match_score=round(s.final_score, 2),
            audio_features=s.audio_features
        ))
    
    detected_mood = None
    if result.detected_mood and not result.detected_mood.is_greeting:
        detected_mood = MoodDetectionResponse(
            mood=result.detected_mood.mood,
            mood_vi=result.detected_mood.mood_vi,
            confidence=round(result.detected_mood.confidence, 2),
            intensity=result.detected_mood.intensity,
            keywords_matched=result.detected_mood.keywords_matched
        )
    
    return ChatMessageResponse(
        status="success",
        detected_mood=detected_mood,
        bot_message=result.bot_message,
        songs=songs,
        playlist_id=result.playlist_id,
        session_id=result.session_id,
        require_mood_selection=result.require_mood_selection
    )


@router.post("/mood", response_model=ChatMessageResponse)
async def select_mood(
    request: ChatChipRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Select mood directly using chips (shorthand for /message with chip input).
    
    **Available Moods:**
    - Vui (Happy)
    - Buồn (Sad)
    - Suy tư (Thoughtful/Stressed)
    - Chill (Relaxed)
    - Năng lượng (Energetic)
    
    **Intensity Levels:**
    - Nhẹ (Low)
    - Vừa (Medium)
    - Mạnh (High)
    """
    orchestrator = get_chat_orchestrator()
    
    result = orchestrator.process_message(
        user_id=user_id,
        mood=request.mood,
        intensity=request.intensity,
        input_type="chip",
        session_id=request.session_id,
        limit=request.limit
    )
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    # Convert to response format (same as /message)
    songs = []
    for s in result.songs:
        songs.append(SongResponse(
            song_id=s.song_id,
            name=s.name,
            artist=s.artist,
            genre=s.genre,
            mood=s.mood,
            reason=s.reason,
            match_score=round(s.final_score, 2),
            audio_features=s.audio_features
        ))
    
    detected_mood = MoodDetectionResponse(
        mood=result.detected_mood.mood,
        mood_vi=result.detected_mood.mood_vi,
        confidence=1.0,
        intensity=result.detected_mood.intensity,
        keywords_matched=[]
    )
    
    return ChatMessageResponse(
        status="success",
        detected_mood=detected_mood,
        bot_message=result.bot_message,
        songs=songs,
        playlist_id=result.playlist_id,
        session_id=result.session_id,
        require_mood_selection=False
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Submit feedback on a song recommendation.
    
    **Feedback Types:**
    - `like` - User enjoyed the song
    - `dislike` - User did not enjoy the song
    - `skip` - User skipped the song
    
    **Effects:**
    - Updates user preferences for personalization
    - Affects future recommendations
    """
    if request.feedback_type not in ('like', 'dislike', 'skip'):
        raise HTTPException(
            status_code=400, 
            detail="feedback_type must be 'like', 'dislike', or 'skip'"
        )
    
    orchestrator = get_chat_orchestrator()
    
    result = orchestrator.process_feedback(
        user_id=user_id,
        song_id=request.song_id,
        feedback_type=request.feedback_type,
        history_id=request.history_id,
        listened_duration=request.listened_duration_seconds
    )
    
    return FeedbackResponse(
        status="success" if result.success else "error",
        message=result.message,
        preference_updated=result.preference_updated
    )


@router.get("/moods")
async def get_available_moods():
    """
    Get list of available moods and intensities.
    
    Use this to populate UI chips.
    """
    from shared.constants import MOODS_VI, MOOD_EMOJI, MOOD_DESCRIPTIONS_VI, INTENSITIES_VI
    
    return {
        "moods": [
            {
                "name": mood,
                "emoji": MOOD_EMOJI.get(mood, "🎵"),
                "description": MOOD_DESCRIPTIONS_VI.get(mood, "")
            }
            for mood in MOODS_VI
        ],
        "intensities": [
            {"name": intensity, "value": intensity}
            for intensity in INTENSITIES_VI
        ]
    }
