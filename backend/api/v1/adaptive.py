"""
=============================================================================
ADAPTIVE RECOMMENDATION API v5.0
=============================================================================

Enhanced endpoints for context-aware adaptive recommendations.

New Endpoints:
- POST /v5/conversation/continue - Continue multi-turn with full context
- POST /v5/recommendation/adaptive - Get adaptive recommendations
- POST /v5/learning/weights/{user_id} - Update personalization weights
- GET /v5/session/{user_id}/status - Get full session status with rewards
- POST /v5/feedback/reward - Submit feedback with reward calculation

Author: MusicMoodBot Team
Version: 5.0.0
=============================================================================
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import time

from backend.api.v1.dependencies import get_current_user_id
from backend.services.conversation.conversation_context import (
    get_context_store,
    ConversationContextMemory,
    ConversationTurn,
)
from backend.services.conversation.emotional_trajectory import (
    get_trajectory_tracker,
    EmotionalTrajectoryTracker,
    EmotionalTrend,
)
from backend.services.conversation.session_reward import (
    get_reward_store,
    SessionRewardCalculator,
    FeedbackType,
)
from backend.services.recommendation.scoring_engine import (
    ScoringEngine,
    ScoredSong,
)
from backend.services.recommendation.cold_start import (
    get_cold_start_handler,
    ColdStartHandler,
    ColdStartTransitionManager,
)
from backend.services.recommendation.weight_adapter import (
    WeightAdapter,
)
from backend.services import get_chat_orchestrator

# AI Service (optional - fallback to rule-based if not available)
try:
    from backend.services.ai.gemini_service import get_gemini_service, AIResponse
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    get_gemini_service = None

router = APIRouter()


# =============================================================================
# ENUMS
# =============================================================================

class FeedbackTypeEnum(str, Enum):
    """Feedback types for reward calculation."""
    LOVE = "love"
    LIKE = "like"
    NEUTRAL = "neutral"
    DISLIKE = "dislike"
    SKIP = "skip"
    FULL_PLAY = "full_play"
    REPEAT = "repeat"
    PLAYLIST_ADD = "playlist_add"
    SHARE = "share"


class ExplanationVerbosity(str, Enum):
    """Explanation verbosity levels."""
    MINIMAL = "minimal"
    CASUAL = "casual"
    DETAILED = "detailed"
    EMOTIONAL = "emotional"


# =============================================================================
# REQUEST MODELS
# =============================================================================

class ContinueConversationRequest(BaseModel):
    """Request for continuing a multi-turn conversation."""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    session_id: Optional[str] = Field(None, description="Existing session ID")
    input_type: str = Field("text", description="Input type: text, emoji, tap, chip")
    include_recommendations: bool = Field(False, description="Include recommendations if ready")
    max_recommendations: int = Field(5, ge=1, le=20)
    emotional_support_mode: bool = Field(False, description="Prioritize emotional comfort")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hôm nay mình cảm thấy hơi buồn...",
                "input_type": "text",
                "include_recommendations": True,
                "max_recommendations": 5,
                "emotional_support_mode": True
            }
        }


class AdaptiveRecommendationRequest(BaseModel):
    """Request for adaptive context-aware recommendations."""
    mood: Optional[str] = Field(None, description="Current/target mood")
    energy_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    valence: Optional[float] = Field(None, ge=-1.0, le=1.0)
    arousal: Optional[float] = Field(None, ge=-1.0, le=1.0)
    limit: int = Field(10, ge=1, le=50)
    use_context_memory: bool = Field(True, description="Use conversation context")
    use_emotional_trajectory: bool = Field(True, description="Consider emotional trend")
    apply_cold_start: bool = Field(True, description="Apply cold start handling")
    diversity_factor: float = Field(0.3, ge=0.0, le=1.0)
    include_explanations: bool = Field(True)
    explanation_verbosity: ExplanationVerbosity = Field(ExplanationVerbosity.CASUAL)
    session_context: Optional[Dict[str, Any]] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "mood": "calm",
                "energy_level": 0.4,
                "limit": 10,
                "use_context_memory": True,
                "use_emotional_trajectory": True,
                "diversity_factor": 0.3,
                "include_explanations": True,
                "explanation_verbosity": "casual"
            }
        }


class RewardFeedbackRequest(BaseModel):
    """Request for submitting feedback with reward calculation."""
    song_id: int = Field(..., description="Song ID")
    feedback_type: FeedbackTypeEnum = Field(..., description="Type of feedback")
    session_id: Optional[str] = Field(None)
    context: Optional[Dict[str, Any]] = Field(None)
    play_duration_seconds: Optional[float] = Field(None, ge=0)
    song_duration_seconds: Optional[float] = Field(None, ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "song_id": 123,
                "feedback_type": "like",
                "play_duration_seconds": 180,
                "song_duration_seconds": 210
            }
        }


class WeightUpdateRequest(BaseModel):
    """Request for updating personalization weights."""
    adjustment_type: str = Field("feedback", description="Type: feedback, explicit, reset")
    feedback_type: Optional[str] = Field(None)
    song_features: Optional[Dict[str, float]] = Field(None)
    explicit_weights: Optional[Dict[str, float]] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "adjustment_type": "feedback",
                "feedback_type": "like",
                "song_features": {
                    "valence": 0.7,
                    "energy": 0.6,
                    "danceability": 0.5
                }
            }
        }


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class ConversationContinueResponse(BaseModel):
    """Response for continue conversation endpoint."""
    session_id: str
    turn_number: int
    bot_response: str
    detected_mood: Optional[str] = None
    mood_confidence: float = 0.0
    emotional_trend: str = "stable"
    comfort_boost_applied: bool = False
    clarity_score: float = 0.0
    context_entities: Dict[str, List[str]] = {}
    should_recommend: bool = False
    recommendations: Optional[List[Dict[str, Any]]] = None
    processing_time_ms: int = 0


class AdaptiveRecommendationResponse(BaseModel):
    """Response for adaptive recommendations."""
    recommendations: List[Dict[str, Any]]
    strategy_used: str
    personalization_weight: float
    cold_start_active: bool
    emotional_trend: str
    context_modifiers: Dict[str, float] = {}
    total_candidates: int
    diversity_applied: bool
    processing_time_ms: int


class RewardFeedbackResponse(BaseModel):
    """Response for reward feedback submission."""
    success: bool
    session_reward_updated: bool
    engagement_score: float
    satisfaction_score: float
    emotional_alignment: float
    total_reward: float
    weights_updated: bool


class SessionStatusResponse(BaseModel):
    """Full session status with rewards."""
    user_id: int
    active_session_id: Optional[str]
    context_memory: Dict[str, Any]
    emotional_trajectory: Dict[str, Any]
    session_rewards: Dict[str, Any]
    personalization_weights: Dict[str, float]
    cold_start_status: Dict[str, Any]


class WeightUpdateResponse(BaseModel):
    """Response for weight update."""
    success: bool
    updated_weights: Dict[str, float]
    adjustment_magnitude: float
    total_adjustments: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/conversation/continue", response_model=ConversationContinueResponse)
async def continue_conversation(
    request: ContinueConversationRequest,
    user_id: int = Depends(get_current_user_id)
) -> ConversationContinueResponse:
    """
    Continue a multi-turn conversation with full context awareness.
    
    This endpoint:
    - Uses Gemini AI for natural language understanding (if available)
    - Tracks conversation context (entities, topics, mood history)
    - Monitors emotional trajectory (improving/declining)
    - Applies comfort music boost if emotional support is needed
    - Returns recommendations when clarity threshold is met
    
    Features:
    - Gemini AI integration for better NLP
    - 10-turn sliding window memory
    - Valence-Arousal emotional tracking
    - Automatic comfort music detection
    """
    start_time = time.time()
    
    # Get services
    context_store = get_context_store()
    trajectory_tracker = get_trajectory_tracker()
    
    # Get or create session context
    session_id = request.session_id or f"session_{user_id}_{int(time.time())}"
    context = context_store.get_user_context(user_id)
    if context is None:
        context = ConversationContextMemory(
            session_id=session_id,
            user_id=user_id,
        )
        context_store.set_user_context(user_id, context)
    
    # Build conversation history for AI
    conversation_history = []
    turns_list = list(context._turns)
    for turn in turns_list[-3:]:  # Last 3 turns
        conversation_history.append({
            "user": turn.user_message,
            "bot": turn.bot_response
        })
    
    # Try Gemini AI first for better understanding
    ai_response = None
    bot_response = None  # Initialize to avoid UnboundLocalError
    should_recommend_ai = None
    
    if AI_AVAILABLE and get_gemini_service:
        try:
            gemini = get_gemini_service()
            ai_response = await gemini.analyze_message(request.message, conversation_history)
        except Exception as e:
            print(f"Gemini AI error: {e}")
            ai_response = None
    
    # Use AI response or fallback to rule-based
    if ai_response and ai_response.detected_mood:
        detected_mood = ai_response.detected_mood
        mood_confidence = ai_response.mood_confidence
        bot_response = ai_response.bot_message
        should_recommend_ai = ai_response.should_recommend
    else:
        # Fallback to rule-based detection
        detected_mood = _detect_mood_from_text(request.message)
        mood_confidence = 0.7 if detected_mood else 0.0
    
    # Extract entities (simplified)
    extracted_entities = _extract_entities(request.message)
    if ai_response and ai_response.suggested_genres:
        extracted_entities["genres"] = ai_response.suggested_genres
    
    # Calculate clarity score based on current context
    clarity_score = _calculate_clarity(context)
    
    # Get emotional trend
    if detected_mood:
        trajectory_tracker.add_mood(user_id, detected_mood)
    
    emotional_trend = trajectory_tracker.get_trend(user_id)
    trend_str = emotional_trend.value if emotional_trend else "stable"
    
    # Check if comfort boost needed
    comfort_boost = 0.0
    if request.emotional_support_mode and emotional_trend == EmotionalTrend.DECLINING:
        comfort_boost = trajectory_tracker.get_comfort_boost(user_id)
    
    # Generate bot response if not from AI
    if not bot_response:
        bot_response = _generate_bot_response(
            context=context,
            detected_mood=detected_mood,
            emotional_trend=trend_str,
            clarity_score=clarity_score,
        )
    
    # Add turn to context using the method interface
    turn = context.add_turn(
        user_message=request.message,
        bot_response=bot_response,
        detected_mood=detected_mood,
        confidence=mood_confidence,
        entities=extracted_entities,
    )
    
    # Get context entities summary
    context_entities = {
        "artists": list(context.accumulated_artists),
        "genres": list(context.accumulated_genres),
        "moods": context.accumulated_moods,
    }
    
    # Update clarity score after adding turn
    clarity_score = _calculate_clarity(context)
    
    # Determine if ready to recommend
    # Use AI decision if available, otherwise use rule-based
    if should_recommend_ai is not None:
        should_recommend = should_recommend_ai
    else:
        should_recommend = clarity_score >= 0.7 or context.turn_count >= 3
    
    recommendations = None
    if should_recommend and request.include_recommendations:
        recommendations = await _get_adaptive_recommendations(
            user_id=user_id,
            mood=detected_mood,
            context=context,
            limit=request.max_recommendations,
            comfort_boost=comfort_boost,
        )
    
    processing_time = int((time.time() - start_time) * 1000)
    
    return ConversationContinueResponse(
        session_id=session_id,
        turn_number=context.turn_count,
        bot_response=bot_response,
        detected_mood=detected_mood,
        mood_confidence=mood_confidence,
        emotional_trend=trend_str,
        comfort_boost_applied=comfort_boost > 0,
        clarity_score=clarity_score,
        context_entities=context_entities,
        should_recommend=should_recommend,
        recommendations=recommendations,
        processing_time_ms=processing_time,
    )


@router.post("/recommendation/adaptive", response_model=AdaptiveRecommendationResponse)
async def get_adaptive_recommendations(
    request: AdaptiveRecommendationRequest,
    user_id: int = Depends(get_current_user_id)
) -> AdaptiveRecommendationResponse:
    """
    Get context-aware adaptive recommendations.
    
    Features:
    - Uses conversation context memory
    - Considers emotional trajectory
    - Applies cold start handling for new users
    - Thompson Sampling for exploration/exploitation
    - Diversity filtering
    """
    start_time = time.time()
    
    # Initialize services
    context_store = get_context_store()
    trajectory_tracker = get_trajectory_tracker()
    cold_start = get_cold_start_handler()
    scoring_engine = ScoringEngine()
    
    # Get context if available
    context = None
    context_modifiers = {}
    if request.use_context_memory:
        context = context_store.get_user_context(user_id)
        if context:
            context_modifiers = context.get_context_modifiers()
    
    # Get emotional trend
    emotional_trend = EmotionalTrend.STABLE
    if request.use_emotional_trajectory:
        emotional_trend = trajectory_tracker.get_trend(user_id) or EmotionalTrend.STABLE
    
    # Check cold start
    cold_start_active = cold_start.is_cold_start(user_id) and request.apply_cold_start
    personalization_weight = cold_start.get_personalization_weight(user_id)
    
    if cold_start_active:
        # Get cold start recommendations
        cold_songs, strategy, pw = cold_start.get_recommendations(
            user_id=user_id,
            mood=request.mood,
            limit=request.limit,
        )
        
        recommendations = [song.to_dict() for song in cold_songs]
        total_candidates = len(cold_songs)
        strategy_used = strategy
    else:
        # Get personalized recommendations via scoring engine
        recommendations, strategy_used, total_candidates = await _score_and_rank(
            user_id=user_id,
            mood=request.mood,
            energy=request.energy_level,
            valence=request.valence,
            arousal=request.arousal,
            limit=request.limit,
            diversity_factor=request.diversity_factor,
            context_modifiers=context_modifiers,
            emotional_trend=emotional_trend,
        )
    
    # Add explanations if requested
    if request.include_explanations:
        recommendations = _add_explanations(
            recommendations=recommendations,
            verbosity=request.explanation_verbosity,
            mood=request.mood,
            emotional_trend=emotional_trend.value,
        )
    
    processing_time = int((time.time() - start_time) * 1000)
    
    return AdaptiveRecommendationResponse(
        recommendations=recommendations[:request.limit],
        strategy_used=strategy_used,
        personalization_weight=personalization_weight,
        cold_start_active=cold_start_active,
        emotional_trend=emotional_trend.value,
        context_modifiers=context_modifiers,
        total_candidates=total_candidates,
        diversity_applied=request.diversity_factor > 0,
        processing_time_ms=processing_time,
    )


@router.post("/feedback/reward", response_model=RewardFeedbackResponse)
async def submit_reward_feedback(
    request: RewardFeedbackRequest,
    user_id: int = Depends(get_current_user_id)
) -> RewardFeedbackResponse:
    """
    Submit feedback with reward calculation for reinforcement learning.
    
    Calculates:
    - Engagement score (play completion, repeats)
    - Satisfaction score (explicit likes/dislikes)
    - Emotional alignment (mood-song match)
    """
    # Get reward calculator
    reward_store = get_reward_store()
    session_id = request.session_id or f"reward_session_{user_id}_{int(time.time())}"
    calculator = reward_store.get_user_calculator(user_id)
    if calculator is None:
        calculator = SessionRewardCalculator(session_id, user_id)
        reward_store.set_user_calculator(user_id, calculator)
    
    # Map feedback type to string (SessionRewardCalculator uses string feedback)
    # Handle extended feedback types by mapping to core types
    feedback_mapping = {
        FeedbackTypeEnum.LOVE: "love",
        FeedbackTypeEnum.LIKE: "like",
        FeedbackTypeEnum.NEUTRAL: "neutral",
        FeedbackTypeEnum.DISLIKE: "dislike",
        FeedbackTypeEnum.SKIP: "skip",
        FeedbackTypeEnum.FULL_PLAY: "like",  # Map to like (positive engagement)
        FeedbackTypeEnum.REPEAT: "love",     # Map to love (strong positive)
        FeedbackTypeEnum.PLAYLIST_ADD: "love",  # Map to love
        FeedbackTypeEnum.SHARE: "love",      # Map to love
    }
    feedback_str = feedback_mapping.get(request.feedback_type, "neutral")
    
    # Calculate play progress as percentage
    listen_duration_pct = 0.0
    if request.play_duration_seconds and request.song_duration_seconds:
        listen_duration_pct = min(100.0, (request.play_duration_seconds / request.song_duration_seconds) * 100)
    
    # Record feedback using correct method signature
    calculator.record_feedback(
        song_id=request.song_id,
        feedback=feedback_str,
        listen_duration_pct=listen_duration_pct,
    )
    
    # Get reward components
    engagement = calculator.calculate_engagement_score()
    satisfaction = calculator.calculate_satisfaction_score()
    emotional = calculator.calculate_emotional_alignment()
    total_reward = calculator.calculate_session_reward()
    
    # Update weights based on feedback
    weight_adapter = WeightAdapter()
    weights_updated = False
    
    # Get song features (would come from database)
    song_features = request.context.get("song_features", {}) if request.context else {}
    
    if song_features:
        weight_adapter.adjust_weights(
            user_id=user_id,
            feedback_type=feedback_str,
            song_features=song_features,
        )
        weights_updated = True
    
    return RewardFeedbackResponse(
        success=True,
        session_reward_updated=True,
        engagement_score=engagement,
        satisfaction_score=satisfaction,
        emotional_alignment=emotional,
        total_reward=total_reward,
        weights_updated=weights_updated,
    )


@router.get("/session/{target_user_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    target_user_id: int = Path(..., description="User ID"),
    user_id: int = Depends(get_current_user_id)
) -> SessionStatusResponse:
    """
    Get comprehensive session status including all v5.0 components.
    """
    # Security: Only allow users to view their own status
    if target_user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot view other user's session")
    
    # Get all components
    context_store = get_context_store()
    trajectory_tracker = get_trajectory_tracker()
    reward_store = get_reward_store()
    cold_start = get_cold_start_handler()
    weight_adapter = WeightAdapter()
    
    # Context memory
    context = context_store.get_user_context(user_id)
    context_data = {
        "turn_count": context.turn_count if context else 0,
        "accumulated_entities": {
            "artists": list(context.accumulated_artists) if context else [],
            "genres": list(context.accumulated_genres) if context else [],
            "moods": list(context.accumulated_moods) if context else [],
        },
        "window_size": context.window_size if context else 10,
    }
    
    # Emotional trajectory
    trend = trajectory_tracker.get_trend(user_id)
    trajectory_data = {
        "current_trend": trend.value if trend else "unknown",
        "data_points": trajectory_tracker.get_history_count(user_id),
    }
    
    # Session rewards
    calculator = reward_store.get_user_calculator(user_id)
    reward_data = {
        "engagement_score": calculator.calculate_engagement_score() if calculator else 0.0,
        "satisfaction_score": calculator.calculate_satisfaction_score() if calculator else 0.0,
        "total_reward": calculator.calculate_session_reward() if calculator else 0.0,
    }
    
    # Personalization weights
    weights = weight_adapter.get_weights(user_id)
    
    # Cold start status
    cold_start_data = {
        "is_cold_start": cold_start.is_cold_start(user_id),
        "personalization_weight": cold_start.get_personalization_weight(user_id),
        "transition_threshold": cold_start.TRANSITION_COMPLETE_AT,
    }
    
    return SessionStatusResponse(
        user_id=user_id,
        active_session_id=f"session_{user_id}" if context else None,
        context_memory=context_data,
        emotional_trajectory=trajectory_data,
        session_rewards=reward_data,
        personalization_weights=weights,
        cold_start_status=cold_start_data,
    )


@router.post("/learning/weights/{target_user_id}", response_model=WeightUpdateResponse)
async def update_weights(
    request: WeightUpdateRequest,
    target_user_id: int = Path(..., description="User ID"),
    user_id: int = Depends(get_current_user_id)
) -> WeightUpdateResponse:
    """
    Update personalization weights for a user.
    
    Supports:
    - feedback: Automatic adjustment based on feedback
    - explicit: Direct weight setting
    - reset: Reset to default weights
    """
    if target_user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot modify other user's weights")
    
    weight_adapter = WeightAdapter()
    
    if request.adjustment_type == "reset":
        weight_adapter.reset_weights(user_id)
        weights = weight_adapter.get_weights(user_id)
        return WeightUpdateResponse(
            success=True,
            updated_weights=weights,
            adjustment_magnitude=0.0,
            total_adjustments=0,
        )
    
    if request.adjustment_type == "explicit" and request.explicit_weights:
        weight_adapter.set_weights(user_id, request.explicit_weights)
        return WeightUpdateResponse(
            success=True,
            updated_weights=request.explicit_weights,
            adjustment_magnitude=0.0,
            total_adjustments=1,
        )
    
    if request.adjustment_type == "feedback" and request.feedback_type and request.song_features:
        old_weights = weight_adapter.get_weights(user_id)
        
        weight_adapter.adjust_weights(
            user_id=user_id,
            feedback_type=request.feedback_type,
            song_features=request.song_features,
        )
        
        new_weights = weight_adapter.get_weights(user_id)
        
        # Calculate adjustment magnitude
        magnitude = sum(
            abs(new_weights.get(k, 0) - old_weights.get(k, 0))
            for k in set(new_weights.keys()) | set(old_weights.keys())
        )
        
        return WeightUpdateResponse(
            success=True,
            updated_weights=new_weights,
            adjustment_magnitude=magnitude,
            total_adjustments=weight_adapter.get_adjustment_count(user_id),
        )
    
    raise HTTPException(
        status_code=400,
        detail="Invalid adjustment request. Provide required fields for adjustment_type."
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _detect_mood_from_text(text: str) -> Optional[str]:
    """Simple mood detection from text."""
    text_lower = text.lower()
    
    mood_keywords = {
        "happy": ["vui", "hạnh phúc", "happy", "tuyệt vời", "phấn khích"],
        "sad": ["buồn", "sad", "chán", "tệ", "khóc", "thất vọng"],
        "calm": ["bình yên", "calm", "thư giãn", "relax", "yên bình"],
        "excited": ["phấn khích", "excited", "hào hứng", "náo nhiệt"],
        "angry": ["tức", "angry", "giận", "bực", "khó chịu"],
        "romantic": ["lãng mạn", "romantic", "yêu", "love", "nhớ"],
        "anxious": ["lo lắng", "anxious", "stress", "căng thẳng"],
        "nostalgic": ["nhớ", "nostalgic", "hoài niệm", "ký ức"],
    }
    
    for mood, keywords in mood_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return mood
    
    return None


def _extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract entities from text (simplified)."""
    entities = {
        "artists": [],
        "genres": [],
        "activities": [],
    }
    
    # Genre keywords
    genres = ["pop", "rock", "jazz", "ballad", "edm", "hip-hop", "r&b", "classical"]
    text_lower = text.lower()
    for genre in genres:
        if genre in text_lower:
            entities["genres"].append(genre)
    
    # Activity keywords
    activities = ["làm việc", "work", "ngủ", "sleep", "tập", "gym", "học", "study", "lái xe", "drive"]
    for activity in activities:
        if activity in text_lower:
            entities["activities"].append(activity)
    
    return entities


def _calculate_clarity(context: ConversationContextMemory) -> float:
    """Calculate conversation clarity score."""
    turns = context.windowed_turns
    if not turns:
        return 0.0
    
    # Factors contributing to clarity
    scores = []
    
    # Mood detection confidence
    mood_confidences = [t.confidence for t in turns if t.confidence and t.confidence > 0]
    if mood_confidences:
        scores.append(sum(mood_confidences) / len(mood_confidences))
    
    # Entity richness
    entity_count = (
        len(context.accumulated_artists) + 
        len(context.accumulated_genres) + 
        len(context.accumulated_moods)
    )
    entity_score = min(1.0, entity_count / 5)
    scores.append(entity_score)
    
    # Turn count contribution
    turn_score = min(1.0, context.turn_count / 3)
    scores.append(turn_score)
    
    return sum(scores) / len(scores) if scores else 0.0


def _generate_bot_response(
    context: ConversationContextMemory,
    detected_mood: Optional[str],
    emotional_trend: str,
    clarity_score: float,
) -> str:
    """Generate contextual bot response in Vietnamese."""
    # Map English moods to Vietnamese
    mood_vi_map = {
        "sad": "buồn", "happy": "vui", "calm": "thư giãn", "excited": "phấn khích",
        "angry": "khó chịu", "stress": "căng thẳng", "energetic": "năng động",
        "romantic": "lãng mạn", "focus": "tập trung", "neutral": "bình thường",
        "anxious": "lo lắng", "lonely": "cô đơn", "tired": "mệt mỏi",
        "nostalgic": "hoài niệm", "chill": "chill", "melancholy": "u sầu"
    }
    mood_vi = mood_vi_map.get(detected_mood, detected_mood) if detected_mood else None
    
    if clarity_score >= 0.7:
        if mood_vi:
            return f"Mình hiểu rồi! Bạn đang cảm thấy {mood_vi}. Để mình gợi ý một vài bài hát phù hợp nhé!"
        return "Mình đã hiểu tâm trạng của bạn. Để mình chọn nhạc cho bạn nhé!"
    
    if not mood_vi:
        return "Bạn có thể chia sẻ thêm về tâm trạng của mình được không?"
    
    if emotional_trend == "declining":
        return f"Mình cảm nhận được bạn đang {mood_vi}. Bạn có muốn nghe nhạc để thư giãn không?"
    
    probing_questions = {
        "sad": "Mình hiểu. Bạn muốn nghe nhạc để đồng cảm hay để vui hơn?",
        "happy": "Thật tuyệt! Bạn muốn nhạc sôi động hay nhẹ nhàng?",
        "calm": "Bạn đang thư giãn nhỉ. Bạn thích thể loại nhạc nào?",
        "excited": "Wow! Bạn muốn nhạc năng lượng cao hay vừa phải?",
        "angry": "Mình hiểu bạn đang khó chịu. Bạn muốn nhạc giúp xả stress hay nhạc nhẹ nhàng?",
        "stress": "Mình cảm nhận được bạn đang căng thẳng. Bạn muốn nhạc để thư giãn không?",
    }
    
    return probing_questions.get(detected_mood, f"Mình thấy bạn đang {mood_vi}. Bạn muốn nghe nhạc như thế nào?")


async def _get_adaptive_recommendations(
    user_id: int,
    mood: Optional[str],
    context: ConversationContextMemory,
    limit: int,
    comfort_boost: float,
) -> List[Dict[str, Any]]:
    """Get adaptive recommendations based on context using ChatOrchestrator."""
    try:
        # Use the same orchestrator as v1 API for consistency
        orchestrator = get_chat_orchestrator()
        
        # Map mood to Vietnamese for orchestrator
        mood_vi_map = {
            "happy": "Vui", "sad": "Buồn", "energetic": "Năng lượng",
            "calm": "Chill", "angry": "Tức giận", "romantic": "Lãng mạn",
            "focus": "Tập trung", "stress": "Căng thẳng", "neutral": "Chill"
        }
        mood_vi = mood_vi_map.get(mood, "Chill") if mood else "Chill"
        
        # Get recommendations via orchestrator
        result = orchestrator.process_message(
            user_id=user_id,
            mood=mood_vi,
            intensity="Vừa",
            input_type="chip",
            limit=limit
        )
        
        if result.success and result.songs:
            recommendations = []
            for song in result.songs:
                recommendations.append({
                    "song_id": song.song_id,
                    "name": song.name,
                    "artist": song.artist,
                    "genre": song.genre,
                    "mood": song.mood,
                    "score": round(song.final_score, 2),
                    "explanation": song.reason,
                    "comfort_boost_applied": comfort_boost > 0,
                    "audio_features": song.audio_features,
                })
            return recommendations
    except Exception as e:
        print(f"Error getting adaptive recommendations: {e}")
    
    # Fallback to cold start handler
    cold_start = get_cold_start_handler()
    if cold_start.is_cold_start(user_id):
        songs, _, _ = cold_start.get_recommendations(user_id, mood, limit)
        return [s.to_dict() for s in songs]
    
    return []


async def _score_and_rank(
    user_id: int,
    mood: Optional[str],
    energy: Optional[float],
    valence: Optional[float],
    arousal: Optional[float],
    limit: int,
    diversity_factor: float,
    context_modifiers: Dict[str, float],
    emotional_trend: EmotionalTrend,
) -> tuple:
    """Score and rank songs using the scoring engine."""
    # Placeholder - would integrate with database and full scoring
    strategy = "adaptive_v5"
    
    recommendations = [
        {
            "song_id": i,
            "name": f"Recommended Song {i}",
            "artist": f"Artist {i}",
            "mood": mood or "neutral",
            "energy": energy or 0.5,
            "valence": valence or 0.0,
            "score": 1.0 - (i * 0.05),
            "strategy": strategy,
        }
        for i in range(1, limit + 1)
    ]
    
    return recommendations, strategy, limit * 2


def _add_explanations(
    recommendations: List[Dict[str, Any]],
    verbosity: ExplanationVerbosity,
    mood: Optional[str],
    emotional_trend: str,
) -> List[Dict[str, Any]]:
    """Add natural language explanations to recommendations."""
    for rec in recommendations:
        mood_str = mood or "current"
        
        if verbosity == ExplanationVerbosity.MINIMAL:
            rec["explanation"] = f"Matches your {mood_str} mood"
        elif verbosity == ExplanationVerbosity.CASUAL:
            rec["explanation"] = f"This {mood_str} track should fit your vibe right now"
        elif verbosity == ExplanationVerbosity.DETAILED:
            rec["explanation"] = (
                f"Selected based on your {mood_str} mood, "
                f"emotional trend ({emotional_trend}), and listening history"
            )
        elif verbosity == ExplanationVerbosity.EMOTIONAL:
            if emotional_trend == "declining":
                rec["explanation"] = f"This comforting track can help lift your spirits"
            else:
                rec["explanation"] = f"A {mood_str} song to match and enhance your mood"
    
    return recommendations
