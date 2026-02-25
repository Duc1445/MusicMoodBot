"""
Advanced Recommendation API Router
===================================
Endpoints for the enhanced recommendation engine v4.0.

Endpoints:
- POST /recommend - Get personalized recommendations
- POST /recommend/explain - Get recommendations with explanations
- GET /recommend/strategies - List available strategies
- POST /recommend/feedback - Submit detailed feedback

Metrics Endpoints:
- GET /metrics/dashboard - Get recommendation metrics dashboard
- GET /metrics/user/{user_id} - Get user-specific metrics
- GET /metrics/experiments - List A/B experiments
- POST /metrics/experiments - Create new experiment

Learning Endpoints:
- GET /learning/drift/{user_id} - Get preference drift analysis
- GET /learning/weights/{user_id} - Get user's feature weights
- POST /learning/weights/{user_id} - Adjust feature weights

Author: MusicMoodBot Team
Version: 4.0.0
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from backend.api.v1.dependencies import get_current_user_id
from backend.repositories import FeedbackRepository
from backend.repositories.feedback_repository import (
    FeedbackContext, 
    PreferenceDrift
)

router = APIRouter()


# =============================================================================
# ENUMS
# =============================================================================

class StrategyType(str, Enum):
    """Available recommendation strategies."""
    EMOTION = "emotion"
    CONTENT = "content"
    COLLABORATIVE = "collaborative"
    DIVERSITY = "diversity"
    EXPLORATION = "exploration"


class ExplanationStyle(str, Enum):
    """Explanation verbosity styles."""
    CASUAL = "casual"
    DETAILED = "detailed"
    MINIMAL = "minimal"
    EMOTIONAL = "emotional"


class ExplorationMethod(str, Enum):
    """Exploration/exploitation balancing methods."""
    THOMPSON = "thompson_sampling"
    UCB1 = "ucb1"
    EPSILON_GREEDY = "epsilon_greedy"
    SOFTMAX = "softmax"


# =============================================================================
# REQUEST MODELS
# =============================================================================

class RecommendationRequest(BaseModel):
    """Request for recommendations."""
    mood: Optional[str] = Field(None, description="Target mood (e.g., happy, calm)")
    energy_level: Optional[float] = Field(None, ge=0.0, le=1.0, description="Target energy 0-1")
    valence: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Target valence -1 to 1")
    limit: int = Field(10, ge=1, le=50, description="Number of recommendations")
    include_explanation: bool = Field(False, description="Include NLG explanations")
    explanation_style: ExplanationStyle = Field(ExplanationStyle.CASUAL)
    strategies: Optional[List[StrategyType]] = Field(
        None, 
        description="Preferred strategies (uses all if not specified)"
    )
    exploration_method: ExplorationMethod = Field(ExplorationMethod.THOMPSON)
    session_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Session context (time_of_day, activity, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "mood": "happy",
                "energy_level": 0.7,
                "limit": 10,
                "include_explanation": True,
                "explanation_style": "casual",
                "strategies": ["emotion", "diversity"],
                "session_context": {
                    "time_of_day": "evening",
                    "activity": "relaxing"
                }
            }
        }


class FeedbackRequest(BaseModel):
    """Request to submit feedback on a recommendation."""
    song_id: int = Field(..., description="Song ID")
    feedback_type: str = Field(
        ..., 
        description="Feedback type: like, dislike, skip, love, neutral"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Contextual information"
    )
    emotional_response: Optional[Dict[str, Any]] = Field(
        None,
        description="User's emotional response"
    )
    listen_duration_pct: Optional[float] = Field(
        None, ge=0.0, le=100.0,
        description="Percentage of song listened"
    )
    recommendation_id: Optional[str] = Field(
        None,
        description="ID of the recommendation this feedback relates to"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "song_id": 42,
                "feedback_type": "like",
                "context": {
                    "mood": "happy",
                    "time_of_day": "morning",
                    "activity": "commute"
                },
                "listen_duration_pct": 85.5
            }
        }


class WeightAdjustmentRequest(BaseModel):
    """Request to adjust feature weights."""
    feature: str = Field(..., description="Feature name to adjust")
    weight: float = Field(..., ge=0.0, le=2.0, description="New weight value")
    reason: Optional[str] = Field(None, description="Reason for adjustment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feature": "mood_match",
                "weight": 1.5,
                "reason": "User prefers mood-matched songs"
            }
        }


class CreateExperimentRequest(BaseModel):
    """Request to create an A/B experiment."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None)
    variant_a_config: Dict[str, Any] = Field(..., description="Configuration for variant A")
    variant_b_config: Dict[str, Any] = Field(..., description="Configuration for variant B")
    traffic_split: float = Field(0.5, ge=0.1, le=0.9, description="Traffic to variant B")
    target_sample_size: int = Field(1000, ge=100, description="Target sample size")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Thompson vs UCB1",
                "description": "Compare exploration methods",
                "variant_a_config": {"exploration_method": "thompson_sampling"},
                "variant_b_config": {"exploration_method": "ucb1"},
                "traffic_split": 0.5,
                "target_sample_size": 1000
            }
        }


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class RecommendedSong(BaseModel):
    """A recommended song with metadata."""
    song_id: int
    name: str
    artist: str
    genre: str
    mood: Optional[str]
    energy: Optional[float]
    valence: Optional[float]
    score: float
    primary_strategy: str
    explanation: Optional[str] = None
    emotional_signals: Optional[List[str]] = None


class RecommendationResponse(BaseModel):
    """Response with recommendations."""
    recommendations: List[RecommendedSong]
    request_id: str
    generated_at: str
    strategies_used: List[str]
    exploration_rate: float
    metrics: Optional[Dict[str, float]] = None


class MetricsDashboard(BaseModel):
    """Metrics dashboard response."""
    precision_at_k: Dict[str, float]
    recall_at_k: Dict[str, float]
    ndcg_at_k: Dict[str, float]
    session_satisfaction: Dict[str, float]
    acceptance_rate: Dict[str, float]
    diversity_metrics: Dict[str, float]
    user_count: int
    recommendation_count: int
    period: str


class DriftAnalysis(BaseModel):
    """Preference drift analysis response."""
    user_id: int
    detected_drifts: List[Dict[str, Any]]
    drift_summary: str
    recommendations: List[str]
    analyzed_at: str


class UserWeights(BaseModel):
    """User's feature weights response."""
    user_id: int
    weights: Dict[str, float]
    last_adjusted: Optional[str]
    adjustment_history: List[Dict[str, Any]]


class ExperimentStatus(BaseModel):
    """A/B experiment status."""
    experiment_id: str
    name: str
    status: str  # running, completed, stopped
    variant_a_samples: int
    variant_b_samples: int
    variant_a_metrics: Dict[str, float]
    variant_b_metrics: Dict[str, float]
    winner: Optional[str]
    statistical_significance: Optional[float]
    created_at: str


# =============================================================================
# RECOMMENDATION ENDPOINTS
# =============================================================================

@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Get personalized song recommendations.
    
    Uses multi-strategy recommendation engine with exploration/exploitation
    balancing to provide diverse, relevant recommendations.
    """
    import uuid
    from datetime import datetime
    
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())[:8]
    
    # TODO: Integrate with actual MultiStrategyEngine
    # For now, return mock response
    mock_recommendations = [
        RecommendedSong(
            song_id=1,
            name="Happy Song",
            artist="Artist A",
            genre="Pop",
            mood="happy",
            energy=0.8,
            valence=0.9,
            score=0.95,
            primary_strategy="emotion",
            explanation="This upbeat track matches your happy mood perfectly!" if request.include_explanation else None,
            emotional_signals=["joy", "energy"] if request.include_explanation else None
        )
    ]
    
    return RecommendationResponse(
        recommendations=mock_recommendations,
        request_id=request_id,
        generated_at=datetime.now().isoformat(),
        strategies_used=[s.value for s in (request.strategies or list(StrategyType))],
        exploration_rate=0.1,
        metrics={"latency_ms": 45.2}
    )


@router.post("/recommend/explain")
async def get_recommendations_with_explanations(
    request: RecommendationRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Get recommendations with detailed natural language explanations.
    
    Returns recommendations along with human-readable explanations
    of why each song was recommended, including emotional signals.
    """
    request.include_explanation = True
    return await get_recommendations(request, user_id)


@router.get("/recommend/strategies")
async def list_strategies():
    """
    List available recommendation strategies with descriptions.
    """
    return {
        "strategies": [
            {
                "id": "emotion",
                "name": "Emotion-Based",
                "description": "Matches songs to your current emotional state using VA space mapping"
            },
            {
                "id": "content",
                "name": "Content-Based",
                "description": "Recommends based on audio features of songs you've liked"
            },
            {
                "id": "collaborative",
                "name": "Collaborative",
                "description": "Suggests songs liked by users with similar tastes"
            },
            {
                "id": "diversity",
                "name": "Diversity-Boosting",
                "description": "Ensures variety in genres, artists, and moods"
            },
            {
                "id": "exploration",
                "name": "Exploration",
                "description": "Discovers new songs outside your usual preferences"
            }
        ],
        "exploration_methods": [
            {
                "id": "thompson_sampling",
                "name": "Thompson Sampling",
                "description": "Bayesian approach balancing exploration with confidence"
            },
            {
                "id": "ucb1",
                "name": "UCB1",
                "description": "Upper Confidence Bound for optimistic exploration"
            },
            {
                "id": "epsilon_greedy",
                "name": "ε-Greedy",
                "description": "Simple random exploration with fixed probability"
            },
            {
                "id": "softmax",
                "name": "Softmax",
                "description": "Temperature-based probabilistic selection"
            }
        ]
    }


# =============================================================================
# FEEDBACK ENDPOINTS
# =============================================================================

@router.post("/recommend/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id)
):
    """
    Submit detailed feedback on a recommendation.
    
    Supports contextual feedback including:
    - Basic feedback type (like, dislike, skip, love, neutral)
    - Contextual information (time, activity, mood)
    - Emotional response
    - Listen duration
    
    Triggers background learning tasks.
    """
    repo = FeedbackRepository()
    
    # Build context
    context = None
    if request.context:
        context = FeedbackContext(
            mood=request.context.get('mood'),
            time_of_day=request.context.get('time_of_day'),
            day_of_week=request.context.get('day_of_week'),
            activity=request.context.get('activity'),
            weather=request.context.get('weather'),
            listen_duration_pct=request.listen_duration_pct,
        )
    
    # Store feedback
    feedback_id = repo.add_with_context(
        user_id=user_id,
        song_id=request.song_id,
        feedback_type=request.feedback_type,
        context=context,
        emotional_response=request.emotional_response,
        session_id=request.recommendation_id,
    )
    
    # Schedule background learning
    background_tasks.add_task(
        _background_learning_update,
        user_id
    )
    
    return {
        "feedback_id": feedback_id,
        "status": "recorded",
        "learning_triggered": True
    }


async def _background_learning_update(user_id: int):
    """Background task to update learning from feedback."""
    repo = FeedbackRepository()
    
    # Auto-adjust weights
    adjustments = repo.auto_adjust_weights_from_feedback(user_id)
    
    # Detect drift
    drifts = repo.detect_preference_drift(user_id)
    
    # Log for monitoring
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Learning update for user {user_id}: "
                f"{len(adjustments)} weight adjustments, {len(drifts)} drifts detected")


# =============================================================================
# METRICS ENDPOINTS
# =============================================================================

@router.get("/metrics/dashboard", response_model=MetricsDashboard)
async def get_metrics_dashboard(
    period: str = Query("7d", description="Time period: 1d, 7d, 30d"),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get recommendation system metrics dashboard.
    
    Returns comprehensive metrics including:
    - Precision@K, Recall@K, NDCG@K
    - Session satisfaction scores
    - Acceptance rates
    - Diversity metrics
    """
    # TODO: Integrate with actual EvaluationEngine
    return MetricsDashboard(
        precision_at_k={"p@5": 0.72, "p@10": 0.65, "p@20": 0.58},
        recall_at_k={"r@5": 0.35, "r@10": 0.52, "r@20": 0.68},
        ndcg_at_k={"ndcg@5": 0.78, "ndcg@10": 0.74, "ndcg@20": 0.71},
        session_satisfaction={
            "avg_score": 0.82,
            "completion_rate": 0.75,
            "return_rate": 0.68
        },
        acceptance_rate={
            "overall": 0.65,
            "first_5": 0.78,
            "position_decay": 0.92
        },
        diversity_metrics={
            "genre_diversity": 0.72,
            "artist_diversity": 0.85,
            "gini_coefficient": 0.35
        },
        user_count=1250,
        recommendation_count=45000,
        period=period
    )


@router.get("/metrics/user/{target_user_id}")
async def get_user_metrics(
    target_user_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Get metrics for a specific user.
    """
    repo = FeedbackRepository()
    
    stats = repo.get_feedback_stats(target_user_id)
    patterns = repo.get_contextual_patterns(target_user_id)
    
    return {
        "user_id": target_user_id,
        "feedback_stats": stats,
        "contextual_patterns": patterns,
        "computed_at": datetime.now().isoformat()
    }


# =============================================================================
# EXPERIMENT ENDPOINTS
# =============================================================================

@router.get("/metrics/experiments")
async def list_experiments(
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: int = Depends(get_current_user_id)
):
    """
    List all A/B experiments.
    """
    # TODO: Integrate with actual experiment tracking
    return {
        "experiments": [
            {
                "experiment_id": "exp_001",
                "name": "Thompson vs UCB1",
                "status": "running",
                "created_at": "2024-01-15T10:00:00Z",
                "progress": 0.45
            }
        ]
    }


@router.post("/metrics/experiments", response_model=ExperimentStatus)
async def create_experiment(
    request: CreateExperimentRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Create a new A/B experiment.
    """
    import uuid
    
    experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
    
    return ExperimentStatus(
        experiment_id=experiment_id,
        name=request.name,
        status="running",
        variant_a_samples=0,
        variant_b_samples=0,
        variant_a_metrics={},
        variant_b_metrics={},
        winner=None,
        statistical_significance=None,
        created_at=datetime.now().isoformat()
    )


@router.get("/metrics/experiments/{experiment_id}", response_model=ExperimentStatus)
async def get_experiment_status(
    experiment_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Get status of a specific experiment.
    """
    # TODO: Fetch from actual experiment tracking
    return ExperimentStatus(
        experiment_id=experiment_id,
        name="Thompson vs UCB1",
        status="running",
        variant_a_samples=523,
        variant_b_samples=498,
        variant_a_metrics={"acceptance_rate": 0.67, "satisfaction": 0.72},
        variant_b_metrics={"acceptance_rate": 0.63, "satisfaction": 0.69},
        winner=None,
        statistical_significance=0.82,
        created_at="2024-01-15T10:00:00Z"
    )


# =============================================================================
# LEARNING ENDPOINTS
# =============================================================================

@router.get("/learning/drift/{target_user_id}", response_model=DriftAnalysis)
async def get_preference_drift(
    target_user_id: int,
    window_days: int = Query(30, ge=7, le=90),
    user_id: int = Depends(get_current_user_id)
):
    """
    Analyze preference drift for a user.
    
    Detects changes in user preferences over time by comparing
    recent feedback to historical patterns.
    """
    repo = FeedbackRepository()
    
    drifts = repo.detect_preference_drift(target_user_id, window_days)
    drift_history = repo.get_drift_history(target_user_id)
    
    # Generate summary
    if not drifts:
        summary = "No significant preference drift detected."
        recommendations = []
    else:
        drift_attrs = [d.attribute for d in drifts]
        summary = f"Detected drift in: {', '.join(drift_attrs)}"
        
        recommendations = []
        for d in drifts:
            if d.direction == 'increase':
                recommendations.append(
                    f"User's preference for {d.attribute} has increased. "
                    f"Consider emphasizing {d.attribute} in recommendations."
                )
            else:
                recommendations.append(
                    f"User's preference for {d.attribute} has decreased. "
                    f"Consider de-emphasizing {d.attribute}."
                )
    
    return DriftAnalysis(
        user_id=target_user_id,
        detected_drifts=[{
            'attribute': d.attribute,
            'old_value': d.old_value,
            'new_value': d.new_value,
            'magnitude': d.drift_magnitude,
            'direction': d.direction
        } for d in drifts],
        drift_summary=summary,
        recommendations=recommendations,
        analyzed_at=datetime.now().isoformat()
    )


@router.get("/learning/weights/{target_user_id}", response_model=UserWeights)
async def get_user_weights(
    target_user_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Get feature weights for a user.
    
    Returns the current weights used in the ranking function
    for this user's recommendations.
    """
    repo = FeedbackRepository()
    
    weights = repo.get_user_weights(target_user_id)
    history = repo.get_weight_adjustment_history(target_user_id, limit=10)
    
    last_adjusted = history[0]['adjusted_at'] if history else None
    
    return UserWeights(
        user_id=target_user_id,
        weights=weights,
        last_adjusted=last_adjusted,
        adjustment_history=history
    )


@router.post("/learning/weights/{target_user_id}")
async def adjust_user_weights(
    target_user_id: int,
    request: WeightAdjustmentRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Manually adjust feature weights for a user.
    
    Use this to fine-tune the recommendation ranking
    based on explicit user preferences.
    """
    repo = FeedbackRepository()
    
    adjustment = repo.adjust_weights(
        user_id=target_user_id,
        feature=request.feature,
        new_weight=request.weight,
        reason=request.reason or "manual_adjustment"
    )
    
    return {
        "status": "adjusted",
        "feature": request.feature,
        "old_weight": adjustment.old_weight,
        "new_weight": adjustment.new_weight,
        "adjusted_at": adjustment.adjusted_at.isoformat()
    }


@router.post("/learning/weights/{target_user_id}/auto")
async def auto_adjust_weights(
    target_user_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Trigger automatic weight adjustment based on feedback patterns.
    
    Analyzes recent feedback and adjusts weights accordingly.
    """
    repo = FeedbackRepository()
    
    adjustments = repo.auto_adjust_weights_from_feedback(target_user_id)
    
    return {
        "status": "completed",
        "adjustments_made": len(adjustments),
        "details": [{
            "feature": a.feature,
            "old_weight": a.old_weight,
            "new_weight": a.new_weight,
            "reason": a.reason
        } for a in adjustments]
    }
