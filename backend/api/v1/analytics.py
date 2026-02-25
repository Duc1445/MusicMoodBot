"""
=============================================================================
ANALYTICS API ENDPOINTS
=============================================================================

REST API endpoints for system analytics and metrics.

Endpoints:
- GET /api/v1/analytics/system - Get system-wide metrics
- GET /api/v1/analytics/sessions - Get session metrics
- GET /api/v1/analytics/recommendations - Get recommendation metrics
- GET /api/v1/analytics/moods - Get mood distribution
- GET /api/v1/analytics/activity - Get hourly activity
- GET /api/v1/analytics/top-songs - Get top recommended songs

Author: MusicMoodBot Team
Version: 3.1.0
=============================================================================
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import os

from .dependencies import get_db_path

# Import analytics engine
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from services.recommendation.analytics_engine import AnalyticsEngine, SystemMetrics

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class SessionMetricsResponse(BaseModel):
    """Session metrics response."""
    total_sessions: int
    completed_sessions: int
    abandoned_sessions: int
    timeout_sessions: int
    average_turns: float
    median_turns: float
    max_turns: int
    average_clarity_at_recommendation: float
    average_session_duration_seconds: float
    completion_rate: float
    sessions_by_final_state: Dict[str, int]


class RecommendationMetricsResponse(BaseModel):
    """Recommendation metrics response."""
    total_recommendations: int
    total_feedback: int
    likes: int
    dislikes: int
    skips: int
    like_ratio: float
    dislike_ratio: float
    skip_ratio: float
    acceptance_rate: float
    average_listen_duration_seconds: float
    completion_rate: float
    feedback_by_mood: Dict[str, Dict[str, int]]
    feedback_by_genre: Dict[str, Dict[str, int]]


class SystemMetricsResponse(BaseModel):
    """System metrics response."""
    period: Dict[str, str]
    users: Dict[str, int]
    sessions: SessionMetricsResponse
    recommendations: RecommendationMetricsResponse
    performance: Dict[str, float]
    content: Dict[str, Any]


class MoodDistributionResponse(BaseModel):
    """Mood distribution response."""
    distribution: Dict[str, int]
    total: int
    period_days: int


class HourlyActivityResponse(BaseModel):
    """Hourly activity response."""
    activity: Dict[int, int]
    peak_hour: int
    total: int
    period_days: int


class TopSongResponse(BaseModel):
    """Top song entry."""
    song_id: int
    song_name: str
    artist: str
    recommend_count: int
    likes: int


class TopSongsResponse(BaseModel):
    """Top songs response."""
    songs: List[TopSongResponse]
    period_days: int


# =============================================================================
# DEPENDENCY
# =============================================================================

def get_analytics_engine(db_path: str = Depends(get_db_path)) -> AnalyticsEngine:
    """Get analytics engine instance."""
    return AnalyticsEngine(db_path)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/system",
    response_model=SystemMetricsResponse,
    summary="Get system metrics",
    description="Get comprehensive system-wide metrics including sessions, recommendations, and performance."
)
async def get_system_metrics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """
    Get system-wide metrics for the specified time period.
    
    Returns:
    - User statistics (total, active, new)
    - Session metrics (turns, clarity, completion)
    - Recommendation metrics (feedback ratios, acceptance)
    - Performance metrics (response time, error rate)
    - Content metrics (catalog coverage)
    """
    try:
        metrics = engine.compute_system_metrics(days=days)
        return metrics.to_dict()
    except Exception as e:
        logger.error(f"Error computing system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/sessions",
    response_model=SessionMetricsResponse,
    summary="Get session metrics",
    description="Get conversation session metrics including turns and completion rates."
)
async def get_session_metrics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """
    Get session-specific metrics.
    
    Returns:
    - Session counts by state
    - Turn statistics (average, median, max)
    - Clarity scores at recommendation
    - Session duration statistics
    """
    try:
        metrics = engine.compute_session_metrics(days=days)
        return metrics.to_dict()
    except Exception as e:
        logger.error(f"Error computing session metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recommendations",
    response_model=RecommendationMetricsResponse,
    summary="Get recommendation metrics",
    description="Get recommendation and feedback metrics."
)
async def get_recommendation_metrics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """
    Get recommendation-specific metrics.
    
    Returns:
    - Total recommendations and feedback
    - Like/dislike/skip ratios
    - Acceptance and completion rates
    - Breakdown by mood and genre
    """
    try:
        metrics = engine.compute_recommendation_metrics(days=days)
        return metrics.to_dict()
    except Exception as e:
        logger.error(f"Error computing recommendation metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/moods",
    response_model=MoodDistributionResponse,
    summary="Get mood distribution",
    description="Get distribution of detected moods in conversations."
)
async def get_mood_distribution(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """
    Get mood distribution for the time period.
    
    Returns:
    - Count of each detected mood
    - Total mood detections
    """
    try:
        distribution = engine.get_mood_distribution(days=days)
        return {
            "distribution": distribution,
            "total": sum(distribution.values()),
            "period_days": days,
        }
    except Exception as e:
        logger.error(f"Error getting mood distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/activity",
    response_model=HourlyActivityResponse,
    summary="Get hourly activity",
    description="Get user activity distribution by hour of day."
)
async def get_hourly_activity(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """
    Get activity by hour of day.
    
    Returns:
    - Session count for each hour (0-23)
    - Peak activity hour
    """
    try:
        activity = engine.get_hourly_activity(days=days)
        peak_hour = max(activity, key=activity.get) if activity else 0
        return {
            "activity": activity,
            "peak_hour": peak_hour,
            "total": sum(activity.values()),
            "period_days": days,
        }
    except Exception as e:
        logger.error(f"Error getting hourly activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/top-songs",
    response_model=TopSongsResponse,
    summary="Get top recommended songs",
    description="Get the most frequently recommended songs."
)
async def get_top_songs(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of songs to return"),
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """
    Get top recommended songs.
    
    Returns:
    - List of top songs with recommendation counts
    - Like counts for each song
    """
    try:
        songs = engine.get_top_recommended_songs(days=days, limit=limit)
        return {
            "songs": songs,
            "period_days": days,
        }
    except Exception as e:
        logger.error(f"Error getting top songs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="Analytics health check",
    description="Check if analytics engine is operational."
)
async def analytics_health(
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """Check analytics engine health."""
    try:
        # Try a simple query
        _ = engine.get_mood_distribution(days=1)
        return {"status": "healthy", "db_path": engine.db_path}
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
