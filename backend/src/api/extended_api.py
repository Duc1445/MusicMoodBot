"""
Extended API routes for playlist, analytics, similarity, and batch operations.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_path() -> str:
    """Get absolute path to music.db."""
    current_file = os.path.abspath(__file__)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    return os.path.join(backend_dir, "src", "database", "music.db")


# ==================== PYDANTIC MODELS ====================

class CreatePlaylistRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    user_id: Optional[str] = None
    mood_filter: Optional[str] = None
    is_public: bool = False
    tags: List[str] = []


class AddSongsRequest(BaseModel):
    song_ids: List[int]
    added_by: Optional[str] = None


class UpdatePlaylistRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class ReorderSongRequest(BaseModel):
    song_id: int
    new_position: int


class MoodTransitionRequest(BaseModel):
    source_mood: str
    target_mood: str
    speed: str = "moderate"  # gradual, moderate, quick


class MoodJourneyRequest(BaseModel):
    duration_minutes: int = 60
    start_mood: Optional[str] = None
    end_mood: Optional[str] = None


class BatchPredictRequest(BaseModel):
    songs: List[Dict[str, Any]]


class BatchSearchRequest(BaseModel):
    queries: List[str]
    limit_per_query: int = 5


# ==================== PLAYLIST ENDPOINTS ====================

@router.post("/playlists")
def create_playlist(request: CreatePlaylistRequest) -> Dict[str, Any]:
    """Create a new playlist."""
    try:
        from backend.src.services.playlist_service import get_playlist_service
        
        service = get_playlist_service(get_db_path())
        playlist = service.create_playlist(
            name=request.name,
            user_id=request.user_id,
            description=request.description,
            mood_filter=request.mood_filter,
            is_public=request.is_public,
            tags=request.tags
        )
        
        return {
            "status": "success",
            "playlist": playlist.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playlists/{playlist_id}")
def get_playlist(playlist_id: str, include_songs: bool = True) -> Dict[str, Any]:
    """Get playlist by ID."""
    try:
        from backend.src.services.playlist_service import get_playlist_service
        
        service = get_playlist_service(get_db_path())
        
        if include_songs:
            result = service.get_playlist_with_songs(playlist_id)
        else:
            playlist = service.get_playlist(playlist_id)
            result = playlist.to_dict() if playlist else None
        
        if not result:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/playlists/{playlist_id}")
def update_playlist(playlist_id: str, request: UpdatePlaylistRequest) -> Dict[str, Any]:
    """Update playlist metadata."""
    try:
        from backend.src.services.playlist_service import get_playlist_service
        
        service = get_playlist_service(get_db_path())
        success = service.update_playlist(
            playlist_id=playlist_id,
            name=request.name,
            description=request.description,
            is_public=request.is_public,
            tags=request.tags
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        return {"status": "success", "message": "Playlist updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/playlists/{playlist_id}")
def delete_playlist(playlist_id: str) -> Dict[str, str]:
    """Delete a playlist."""
    try:
        from backend.src.services.playlist_service import get_playlist_service
        
        service = get_playlist_service(get_db_path())
        success = service.delete_playlist(playlist_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        return {"status": "success", "message": "Playlist deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playlists/user/{user_id}")
def get_user_playlists(user_id: str) -> Dict[str, Any]:
    """Get all playlists for a user."""
    try:
        from backend.src.services.playlist_service import get_playlist_service
        
        service = get_playlist_service(get_db_path())
        playlists = service.get_user_playlists(user_id)
        
        return {
            "user_id": user_id,
            "playlists": [p.to_dict() for p in playlists],
            "count": len(playlists)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playlists/public")
def get_public_playlists(limit: int = 20) -> Dict[str, Any]:
    """Get public playlists."""
    try:
        from backend.src.services.playlist_service import get_playlist_service
        
        service = get_playlist_service(get_db_path())
        playlists = service.get_public_playlists(limit)
        
        return {
            "playlists": [p.to_dict() for p in playlists],
            "count": len(playlists)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playlists/{playlist_id}/songs")
def add_songs_to_playlist(playlist_id: str, request: AddSongsRequest) -> Dict[str, Any]:
    """Add songs to a playlist."""
    try:
        from backend.src.services.playlist_service import get_playlist_service
        
        service = get_playlist_service(get_db_path())
        added = service.add_songs_batch(
            playlist_id=playlist_id,
            song_ids=request.song_ids,
            added_by=request.added_by
        )
        
        return {
            "status": "success",
            "added_count": added,
            "requested": len(request.song_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/playlists/{playlist_id}/songs/{song_id}")
def remove_song_from_playlist(playlist_id: str, song_id: int) -> Dict[str, str]:
    """Remove a song from a playlist."""
    try:
        from backend.src.services.playlist_service import get_playlist_service
        
        service = get_playlist_service(get_db_path())
        success = service.remove_song(playlist_id, song_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Song not in playlist")
        
        return {"status": "success", "message": "Song removed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playlists/{playlist_id}/reorder")
def reorder_playlist_song(playlist_id: str, request: ReorderSongRequest) -> Dict[str, str]:
    """Move a song to a new position in the playlist."""
    try:
        from backend.src.services.playlist_service import get_playlist_service
        
        service = get_playlist_service(get_db_path())
        success = service.reorder_songs(playlist_id, request.song_id, request.new_position)
        
        if not success:
            raise HTTPException(status_code=404, detail="Song not found in playlist")
        
        return {"status": "success", "message": "Song reordered"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playlists/auto/mood/{mood}")
def create_mood_playlist(
    mood: str,
    user_id: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """Auto-generate a playlist based on mood."""
    try:
        from backend.src.services.playlist_service import get_playlist_service
        
        service = get_playlist_service(get_db_path())
        playlist = service.create_mood_playlist(mood, user_id, limit)
        
        return {
            "status": "success",
            "playlist": playlist.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SIMILARITY ENDPOINTS ====================

@router.get("/songs/{song_id}/similar")
def get_similar_songs(
    song_id: int,
    limit: int = 10,
    exclude_same_artist: bool = False
) -> Dict[str, Any]:
    """Get songs similar to a given song."""
    try:
        from backend.src.pipelines.song_similarity import SongSimilarityEngine
        from backend.src.repo.song_repo import connect, fetch_songs, fetch_song_by_id
        
        con = connect(get_db_path())
        target = fetch_song_by_id(con, song_id)
        
        if not target:
            con.close()
            raise HTTPException(status_code=404, detail="Song not found")
        
        all_songs = fetch_songs(con)
        con.close()
        
        engine = SongSimilarityEngine()
        results = engine.find_similar_songs(
            target, all_songs, limit, exclude_same_artist
        )
        
        return {
            "source_song": {
                "song_id": target.get("song_id"),
                "song_name": target.get("song_name"),
                "artist": target.get("artist")
            },
            "similar_songs": [r.to_dict() for r in results],
            "count": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/songs/{song_id}/similar/diverse")
def get_diverse_similar_songs(
    song_id: int,
    limit: int = 10,
    diversity_weight: float = 0.3
) -> Dict[str, Any]:
    """Get similar songs with diversity (MMR-style selection)."""
    try:
        from backend.src.pipelines.song_similarity import SongSimilarityEngine
        from backend.src.repo.song_repo import connect, fetch_songs, fetch_song_by_id
        
        con = connect(get_db_path())
        target = fetch_song_by_id(con, song_id)
        
        if not target:
            con.close()
            raise HTTPException(status_code=404, detail="Song not found")
        
        all_songs = fetch_songs(con)
        con.close()
        
        engine = SongSimilarityEngine()
        results = engine.find_diverse_similar(
            target, all_songs, limit, diversity_weight
        )
        
        return {
            "source_song": {
                "song_id": target.get("song_id"),
                "song_name": target.get("song_name"),
                "artist": target.get("artist")
            },
            "similar_songs": [r.to_dict() for r in results],
            "diversity_weight": diversity_weight
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/analytics/songs")
def get_song_analytics() -> Dict[str, Any]:
    """Get overall song analytics."""
    try:
        from backend.src.services.analytics_service import get_analytics_service
        
        service = get_analytics_service(get_db_path())
        return service.get_song_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/moods")
def get_mood_analytics() -> Dict[str, Any]:
    """Get detailed mood analytics."""
    try:
        from backend.src.services.analytics_service import get_analytics_service
        
        service = get_analytics_service(get_db_path())
        return service.get_mood_breakdown()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/user/{user_id}")
def get_user_analytics(user_id: str) -> Dict[str, Any]:
    """Get analytics for a specific user."""
    try:
        from backend.src.services.analytics_service import get_analytics_service
        
        service = get_analytics_service(get_db_path())
        return service.get_user_stats(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/user/{user_id}/trend")
def get_user_listening_trend(
    user_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """Get user's listening trend over time."""
    try:
        from backend.src.services.analytics_service import get_analytics_service
        
        service = get_analytics_service(get_db_path())
        trend = service.get_user_listening_trend(user_id, days)
        
        return {
            "user_id": user_id,
            "days": days,
            "trend": trend
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/trending")
def get_trending_songs(days: int = 7, limit: int = 10) -> Dict[str, Any]:
    """Get trending songs."""
    try:
        from backend.src.services.analytics_service import get_analytics_service
        
        service = get_analytics_service(get_db_path())
        trending = service.get_trending_songs(days, limit)
        
        return {
            "period_days": days,
            "trending_songs": trending
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/dashboard")
def get_dashboard() -> Dict[str, Any]:
    """Get dashboard summary data."""
    try:
        from backend.src.services.analytics_service import get_analytics_service
        
        service = get_analytics_service(get_db_path())
        return service.get_dashboard_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/insights")
def get_insights() -> Dict[str, Any]:
    """Get actionable insights."""
    try:
        from backend.src.services.analytics_service import get_analytics_service
        
        service = get_analytics_service(get_db_path())
        insights = service.generate_insights()
        
        return {
            "insights": insights,
            "count": len(insights)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MOOD TRANSITION ENDPOINTS ====================

@router.post("/mood/transition")
def calculate_mood_transition(request: MoodTransitionRequest) -> Dict[str, Any]:
    """Calculate transition path between two moods."""
    try:
        from backend.src.pipelines.mood_transition import get_transition_engine, TransitionSpeed
        
        speed_map = {
            "gradual": TransitionSpeed.GRADUAL,
            "moderate": TransitionSpeed.MODERATE,
            "quick": TransitionSpeed.QUICK,
        }
        
        engine = get_transition_engine()
        transition = engine.calculate_transition(
            request.source_mood,
            request.target_mood,
            speed_map.get(request.speed, TransitionSpeed.MODERATE)
        )
        
        return transition.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mood/transition/playlist")
def get_transition_playlist(
    request: MoodTransitionRequest,
    songs_per_step: int = 2
) -> Dict[str, Any]:
    """Generate a playlist for mood transition."""
    try:
        from backend.src.pipelines.mood_transition import get_transition_engine, TransitionSpeed
        from backend.src.repo.song_repo import connect, fetch_songs
        
        speed_map = {
            "gradual": TransitionSpeed.GRADUAL,
            "moderate": TransitionSpeed.MODERATE,
            "quick": TransitionSpeed.QUICK,
        }
        
        con = connect(get_db_path())
        all_songs = fetch_songs(con)
        con.close()
        
        engine = get_transition_engine()
        playlist = engine.get_transition_playlist(
            request.source_mood,
            request.target_mood,
            all_songs,
            speed_map.get(request.speed, TransitionSpeed.MODERATE),
            songs_per_step
        )
        
        return {
            "source_mood": request.source_mood,
            "target_mood": request.target_mood,
            "speed": request.speed,
            "playlist": playlist,
            "song_count": len(playlist)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mood/{mood}/suggestions")
def get_mood_suggestions(
    mood: str,
    time_of_day: Optional[str] = None
) -> Dict[str, Any]:
    """Get suggested next moods."""
    try:
        from backend.src.pipelines.mood_transition import get_transition_engine
        
        engine = get_transition_engine()
        suggestions = engine.suggest_next_mood(mood, time_of_day)
        
        return {
            "current_mood": mood,
            "time_of_day": time_of_day,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mood/journey")
def plan_mood_journey(request: MoodJourneyRequest) -> Dict[str, Any]:
    """Plan a complete mood journey."""
    try:
        from backend.src.pipelines.mood_transition import get_transition_engine
        
        engine = get_transition_engine()
        journey = engine.get_mood_journey(
            request.duration_minutes,
            request.start_mood,
            request.end_mood
        )
        
        return journey
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BATCH OPERATIONS ====================

@router.post("/batch/predict")
def batch_predict_moods(request: BatchPredictRequest) -> Dict[str, Any]:
    """Predict moods for multiple songs at once."""
    try:
        from backend.src.services.mood_services import DBMoodEngine
        
        engine = DBMoodEngine(db_path=get_db_path())
        engine.fit(force=True)
        
        results = []
        for song in request.songs:
            try:
                pred = engine.predict_one(song)
                results.append({
                    "input": song,
                    "prediction": pred,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "input": song,
                    "error": str(e),
                    "status": "error"
                })
        
        success_count = sum(1 for r in results if r["status"] == "success")
        
        return {
            "results": results,
            "total": len(results),
            "successful": success_count,
            "failed": len(results) - success_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/search")
def batch_search(request: BatchSearchRequest) -> Dict[str, Any]:
    """Search for multiple queries at once."""
    try:
        from backend.src.search.tfidf_search import create_search_engine
        from backend.src.repo.song_repo import connect, fetch_songs
        
        con = connect(get_db_path())
        all_songs = fetch_songs(con)
        con.close()
        
        search_engine = create_search_engine(all_songs)
        
        results = {}
        for query in request.queries:
            try:
                matches = search_engine.search(query, top_k=request.limit_per_query)
                results[query] = {
                    "songs": matches,
                    "count": len(matches)
                }
            except Exception as e:
                results[query] = {
                    "error": str(e),
                    "songs": []
                }
        
        return {
            "queries": len(request.queries),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CACHE MANAGEMENT ====================

@router.get("/cache/stats")
def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    try:
        from backend.src.services.cache_service import get_all_cache_stats
        return get_all_cache_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
def clear_cache(cache_name: Optional[str] = None) -> Dict[str, str]:
    """Clear cache entries."""
    try:
        from backend.src.services.cache_service import get_cache, invalidate_cache
        
        if cache_name:
            count = invalidate_cache(cache_name)
            return {"status": "success", "message": f"Cleared {count} entries from {cache_name}"}
        else:
            # Clear all caches
            from backend.src.services.cache_service import _caches
            total = 0
            for name in list(_caches.keys()):
                total += invalidate_cache(name)
            return {"status": "success", "message": f"Cleared {total} entries from all caches"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TIME-BASED RECOMMENDATIONS ====================

class ActivityRequest(BaseModel):
    activity: str = Field(..., description="Activity name: waking_up, working, exercising, etc.")
    limit: int = 10


class DayScheduleRequest(BaseModel):
    activities: Optional[List[Dict[str, Any]]] = None


class DurationPlaylistRequest(BaseModel):
    duration_minutes: int = Field(..., gt=0)
    activity: Optional[str] = None


class WeatherRequest(BaseModel):
    condition: str = Field(..., description="Weather: sunny, cloudy, rainy, etc.")
    temperature: Optional[int] = None
    humidity: Optional[int] = None
    limit: int = 10


@router.get("/recommendations/now")
def get_recommendations_now(limit: int = 10) -> Dict[str, Any]:
    """Get music recommendations for current time."""
    try:
        from backend.src.services.time_recommender import TimeBasedRecommender
        
        recommender = TimeBasedRecommender(get_db_path())
        rec = recommender.recommend_for_now(limit)
        
        return {
            "status": "success",
            "context": {
                "time_of_day": rec.context.time_of_day.value,
                "hour": rec.context.hour,
                "is_weekend": rec.context.is_weekend
            },
            "suggested_moods": rec.suggested_moods,
            "reason": rec.reason,
            "songs": rec.songs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations/activity")
def get_recommendations_for_activity(request: ActivityRequest) -> Dict[str, Any]:
    """Get recommendations for specific activity."""
    try:
        from backend.src.services.time_recommender import TimeBasedRecommender, Activity
        
        recommender = TimeBasedRecommender(get_db_path())
        
        try:
            activity = Activity(request.activity)
        except ValueError:
            valid_activities = [a.value for a in Activity]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid activity. Valid options: {valid_activities}"
            )
        
        rec = recommender.recommend_for_activity(activity, request.limit)
        
        return {
            "status": "success",
            "activity": request.activity,
            "suggested_moods": rec.suggested_moods,
            "energy_range": rec.energy_range,
            "reason": rec.reason,
            "songs": rec.songs
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/hour/{hour}")
def get_recommendations_for_hour(hour: int, limit: int = 10) -> Dict[str, Any]:
    """Get recommendations for specific hour (0-23)."""
    if hour < 0 or hour > 23:
        raise HTTPException(status_code=400, detail="Hour must be 0-23")
    
    try:
        from backend.src.services.time_recommender import TimeBasedRecommender
        
        recommender = TimeBasedRecommender(get_db_path())
        rec = recommender.recommend_for_time(hour, limit)
        
        return {
            "status": "success",
            "hour": hour,
            "time_of_day": rec.context.time_of_day.value,
            "suggested_moods": rec.suggested_moods,
            "reason": rec.reason,
            "songs": rec.songs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations/day-schedule")
def get_day_schedule(request: DayScheduleRequest) -> Dict[str, Any]:
    """Get music recommendations for entire day."""
    try:
        from backend.src.services.time_recommender import TimeBasedRecommender
        
        recommender = TimeBasedRecommender(get_db_path())
        schedule = recommender.get_day_schedule(request.activities)
        
        return {
            "status": "success",
            "schedule": schedule
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations/duration")
def get_playlist_for_duration(request: DurationPlaylistRequest) -> Dict[str, Any]:
    """Generate playlist for specific duration."""
    try:
        from backend.src.services.time_recommender import TimeBasedRecommender, Activity
        
        recommender = TimeBasedRecommender(get_db_path())
        
        activity = None
        if request.activity:
            try:
                activity = Activity(request.activity)
            except ValueError:
                pass
        
        result = recommender.get_playlist_for_duration(
            request.duration_minutes,
            activity
        )
        
        return {
            "status": "success",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations/weather")
def get_recommendations_for_weather(request: WeatherRequest) -> Dict[str, Any]:
    """Get recommendations based on weather."""
    try:
        from backend.src.services.time_recommender import (
            WeatherBasedRecommender, WeatherContext
        )
        
        recommender = WeatherBasedRecommender(get_db_path())
        weather_ctx = WeatherContext(
            condition=request.condition,
            temperature=request.temperature,
            humidity=request.humidity
        )
        
        result = recommender.recommend_for_weather(weather_ctx, request.limit)
        
        return {
            "status": "success",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== USER PREFERENCES & LEARNING ====================

class RecordInteractionRequest(BaseModel):
    user_id: int
    song_id: int
    event_type: str = Field(..., description="play, like, dislike, skip, complete")
    duration_seconds: Optional[int] = None
    context: Optional[Dict] = None


class PersonalizedRecommendRequest(BaseModel):
    user_id: int
    limit: int = 10
    mood_filter: Optional[str] = None


@router.post("/users/interactions")
def record_user_interaction(request: RecordInteractionRequest) -> Dict[str, Any]:
    """Record user interaction for learning preferences."""
    try:
        from backend.src.services.preference_learning import (
            UserPreferenceLearner, InteractionEvent
        )
        
        learner = UserPreferenceLearner(get_db_path())
        
        event = InteractionEvent(
            user_id=request.user_id,
            song_id=request.song_id,
            event_type=request.event_type,
            duration_seconds=request.duration_seconds,
            context=request.context
        )
        
        learner.record_interaction(event)
        
        return {
            "status": "success",
            "message": "Interaction recorded"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/preferences")
def get_user_preferences(user_id: int) -> Dict[str, Any]:
    """Get user preference profile."""
    try:
        from backend.src.services.preference_learning import UserPreferenceLearner
        
        learner = UserPreferenceLearner(get_db_path())
        prefs = learner.get_preferences(user_id)
        
        return {
            "status": "success",
            "preferences": {
                "user_id": prefs.user_id,
                "favorite_moods": prefs.favorite_moods,
                "favorite_genres": prefs.favorite_genres,
                "favorite_artists": prefs.favorite_artists,
                "energy_preference": prefs.energy_preference,
                "tempo_preference": prefs.tempo_preference,
                "liked_count": len(prefs.liked_songs),
                "disliked_count": len(prefs.disliked_songs)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/personalized-recommendations")
def get_personalized_recommendations(
    request: PersonalizedRecommendRequest
) -> Dict[str, Any]:
    """Get personalized recommendations based on user preferences."""
    try:
        from backend.src.services.preference_learning import UserPreferenceLearner
        
        learner = UserPreferenceLearner(get_db_path())
        songs = learner.get_personalized_recommendations(
            request.user_id,
            request.limit,
            request.mood_filter
        )
        
        return {
            "status": "success",
            "user_id": request.user_id,
            "songs": songs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/similar-users")
def get_similar_users(user_id: int, limit: int = 5) -> Dict[str, Any]:
    """Find users with similar preferences."""
    try:
        from backend.src.services.preference_learning import UserPreferenceLearner
        
        learner = UserPreferenceLearner(get_db_path())
        similar = learner.get_similar_users(user_id, limit)
        
        return {
            "status": "success",
            "user_id": user_id,
            "similar_users": similar
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/stats")
def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Get user listening statistics."""
    try:
        from backend.src.services.preference_learning import UserPreferenceLearner
        
        learner = UserPreferenceLearner(get_db_path())
        stats = learner.get_user_stats(user_id)
        
        return {
            "status": "success",
            **stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}/preferences")
def clear_user_preferences(user_id: int) -> Dict[str, Any]:
    """Clear user preferences (reset)."""
    try:
        from backend.src.services.preference_learning import UserPreferenceLearner
        
        learner = UserPreferenceLearner(get_db_path())
        learner.clear_preferences(user_id)
        
        return {
            "status": "success",
            "message": f"Preferences cleared for user {user_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== EXPORT/IMPORT ====================

class ExportRequest(BaseModel):
    format: str = Field("json", description="Export format: json or csv")
    mood_filter: Optional[str] = None


class ImportRequest(BaseModel):
    file_path: str
    update_existing: bool = False


@router.post("/export/songs")
def export_songs(request: ExportRequest) -> Dict[str, Any]:
    """Export songs to file."""
    try:
        from backend.src.services.export_service import DataExportService, ExportFormat
        
        service = DataExportService(get_db_path())
        
        if request.mood_filter:
            result = service.export_by_mood(
                request.mood_filter,
                ExportFormat(request.format)
            )
        else:
            if request.format == "csv":
                result = service.export_to_csv()
            else:
                result = service.export_to_json()
        
        return {
            "status": "success" if result.success else "error",
            **result.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/songs")
def import_songs(request: ImportRequest) -> Dict[str, Any]:
    """Import songs from file."""
    try:
        from backend.src.services.export_service import DataExportService
        
        service = DataExportService(get_db_path())
        
        if request.file_path.endswith(".csv"):
            result = service.import_from_csv(
                request.file_path,
                request.update_existing
            )
        else:
            result = service.import_from_json(
                request.file_path,
                request.update_existing
            )
        
        return {
            "status": "success" if result.success else "error",
            **result.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/create")
def create_backup() -> Dict[str, Any]:
    """Create database backup."""
    try:
        from backend.src.services.export_service import DataExportService
        
        service = DataExportService(get_db_path())
        result = service.create_backup()
        
        return {
            "status": "success" if result.success else "error",
            **result.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backup/list")
def list_backups() -> Dict[str, Any]:
    """List available backups."""
    try:
        from backend.src.services.export_service import DataExportService
        
        service = DataExportService(get_db_path())
        backups = service.list_backups()
        
        return {
            "status": "success",
            "backups": backups
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/list")
def list_exports() -> Dict[str, Any]:
    """List exported files."""
    try:
        from backend.src.services.export_service import DataExportService
        
        service = DataExportService(get_db_path())
        exports = service.list_exports()
        
        return {
            "status": "success",
            "exports": exports
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DATABASE OPTIMIZATION ====================

@router.get("/db/stats")
def get_database_stats() -> Dict[str, Any]:
    """Get database connection pool statistics."""
    try:
        from backend.src.repo.db_pool import get_pool
        
        pool = get_pool(get_db_path())
        
        return {
            "status": "success",
            "pool_stats": pool.stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/db/optimize")
def optimize_database() -> Dict[str, Any]:
    """Run database optimization (VACUUM, ANALYZE)."""
    try:
        import sqlite3
        
        con = sqlite3.connect(get_db_path())
        cur = con.cursor()
        
        # Run optimizations
        cur.execute("VACUUM")
        cur.execute("ANALYZE")
        
        con.close()
        
        return {
            "status": "success",
            "message": "Database optimized"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HEALTH & INFO ====================

@router.get("/extended/health")
def extended_health_check() -> Dict[str, Any]:
    """Extended health check with service status."""
    status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check database
    try:
        from backend.src.repo.song_repo import connect
        con = connect(get_db_path())
        con.close()
        status["services"]["database"] = "ok"
    except Exception as e:
        status["services"]["database"] = f"error: {str(e)}"
        status["status"] = "degraded"
    
    # Check playlist service
    try:
        from backend.src.services.playlist_service import get_playlist_service
        get_playlist_service(get_db_path())
        status["services"]["playlist"] = "ok"
    except Exception as e:
        status["services"]["playlist"] = f"error: {str(e)}"
    
    # Check analytics service
    try:
        from backend.src.services.analytics_service import get_analytics_service
        get_analytics_service(get_db_path())
        status["services"]["analytics"] = "ok"
    except Exception as e:
        status["services"]["analytics"] = f"error: {str(e)}"
    
    # Check time recommender
    try:
        from backend.src.services.time_recommender import TimeBasedRecommender
        TimeBasedRecommender(get_db_path())
        status["services"]["time_recommender"] = "ok"
    except Exception as e:
        status["services"]["time_recommender"] = f"error: {str(e)}"
    
    # Check preference learner
    try:
        from backend.src.services.preference_learning import UserPreferenceLearner
        UserPreferenceLearner(get_db_path())
        status["services"]["preference_learner"] = "ok"
    except Exception as e:
        status["services"]["preference_learner"] = f"error: {str(e)}"
    
    # Check export service
    try:
        from backend.src.services.export_service import DataExportService
        DataExportService(get_db_path())
        status["services"]["export"] = "ok"
    except Exception as e:
        status["services"]["export"] = f"error: {str(e)}"
    
    return status


@router.get("/extended/endpoints")
def list_extended_endpoints() -> Dict[str, Any]:
    """List all extended API endpoints."""
    return {
        "version": "2.0.0",
        "categories": {
            "playlists": [
                "POST /playlists - Create playlist",
                "GET /playlists/{id} - Get playlist",
                "PUT /playlists/{id} - Update playlist",
                "DELETE /playlists/{id} - Delete playlist",
                "POST /playlists/{id}/songs - Add songs",
                "DELETE /playlists/{id}/songs/{song_id} - Remove song",
                "POST /playlists/auto/mood/{mood} - Auto-generate mood playlist"
            ],
            "similarity": [
                "GET /songs/{id}/similar - Find similar songs",
                "GET /songs/{id}/similar/diverse - Find diverse similar songs"
            ],
            "analytics": [
                "GET /analytics/songs - Song statistics",
                "GET /analytics/moods - Mood breakdown",
                "GET /analytics/dashboard - Full dashboard",
                "GET /analytics/insights - AI insights"
            ],
            "mood_transition": [
                "POST /mood/transition - Calculate transition path",
                "POST /mood/journey - Generate mood journey"
            ],
            "time_recommendations": [
                "GET /recommendations/now - Current time recommendations",
                "POST /recommendations/activity - Activity-based",
                "GET /recommendations/hour/{hour} - Hour-based",
                "POST /recommendations/day-schedule - Full day schedule",
                "POST /recommendations/duration - Duration-based playlist",
                "POST /recommendations/weather - Weather-based"
            ],
            "user_preferences": [
                "POST /users/interactions - Record interaction",
                "GET /users/{id}/preferences - Get preferences",
                "POST /users/personalized-recommendations - Personalized recs",
                "GET /users/{id}/similar-users - Similar users",
                "GET /users/{id}/stats - User statistics"
            ],
            "export_import": [
                "POST /export/songs - Export songs",
                "POST /import/songs - Import songs",
                "POST /backup/create - Create backup",
                "GET /backup/list - List backups",
                "GET /export/list - List exports"
            ],
            "database": [
                "GET /db/stats - Pool statistics",
                "POST /db/optimize - Optimize database"
            ],
            "batch": [
                "POST /batch/predict - Batch mood prediction",
                "POST /batch/search - Batch search"
            ],
            "cache": [
                "GET /cache/stats - Cache statistics",
                "POST /cache/clear - Clear cache"
            ]
        }
    }
