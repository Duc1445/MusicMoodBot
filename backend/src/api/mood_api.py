"""FastAPI routes for mood prediction, search, and ranking."""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
import os

from backend.src.services.mood_services import DBMoodEngine
from backend.src.services.constants import MOODS, Song
from backend.src.search.tfidf_search import TFIDFSearchEngine, create_search_engine
from backend.src.ranking.preference_model import PreferenceModel, UserPreferenceTracker
from backend.src.services.history_service import HistoryService
from backend.src.services.ranking_service import RankingService

router = APIRouter()

# Initialize components globally
_engine: Optional[DBMoodEngine] = None
_search_engine: Optional[TFIDFSearchEngine] = None
_user_trackers: Dict[str, UserPreferenceTracker] = {}
_history_service: Optional[HistoryService] = None
_ranking_service: Optional[RankingService] = None


def get_db_path() -> str:
    """Get absolute path to music.db in backend/src/database directory."""
    current_file = os.path.abspath(__file__)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    return os.path.join(backend_dir, "src", "database", "music.db")


def get_engine() -> DBMoodEngine:
    """Get or create the mood engine instance."""
    global _engine
    if _engine is None:
        _engine = DBMoodEngine(db_path=get_db_path(), add_debug_cols=True, auto_fit=True)
        _engine.fit(force=True)
    return _engine


def get_search_engine() -> TFIDFSearchEngine:
    """Get or create the search engine instance."""
    global _search_engine
    if _search_engine is None:
        from backend.src.repo.song_repo import connect, fetch_songs
        con = connect(get_db_path())
        songs = fetch_songs(con)
        con.close()
        _search_engine = create_search_engine(songs)
    return _search_engine


def get_user_tracker(user_id: str) -> UserPreferenceTracker:
    """Get or create user preference tracker."""
    global _user_trackers
    if user_id not in _user_trackers:
        _user_trackers[user_id] = UserPreferenceTracker(user_id)
    return _user_trackers[user_id]


def get_history_service() -> HistoryService:
    """Get or create history service instance."""
    global _history_service
    if _history_service is None:
        _history_service = HistoryService(get_db_path())
    return _history_service


def get_ranking_service() -> RankingService:
    """Get or create ranking service instance."""
    global _ranking_service
    if _ranking_service is None:
        from backend.src.ranking.preference_model import PreferenceModel
        _ranking_service = RankingService(PreferenceModel())
    return _ranking_service


# ==================== PYDANTIC MODELS ====================

class TextInput(BaseModel):
    """Request body for text input."""
    text: str


class SmartRecommendRequest(BaseModel):
    """Request body for smart recommendation."""
    text: str
    user_id: Optional[str] = None
    limit: int = 10


@router.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "mood-engine"}


@router.post("/predict")
def predict_mood(song: Song) -> Dict[str, object]:
    """
    Predict mood for a single song.
    
    Expected fields in song dict:
    - energy (0-100)
    - valence (0-100)
    - tempo (BPM)
    - loudness (dBFS)
    - danceability (0-100)
    - acousticness (0-100)
    - genre (optional)
    """
    try:
        engine = get_engine()
        result = engine.predict_one(song)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/songs/by-mood/{mood}")
def get_songs_by_mood(
    mood: str,
    db_path: str = Query(None)
) -> List[Dict]:
    """Get all songs with a specific mood."""
    if mood not in MOODS:
        raise HTTPException(status_code=400, detail=f"Invalid mood. Must be one of: {MOODS}")
    
    try:
        from backend.src.repo.song_repo import connect, fetch_songs
        if db_path is None:
            db_path = get_db_path()
        con = connect(db_path)
        songs = fetch_songs(con, "mood = ?", (mood,))
        con.close()
        return songs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/update-missing")
def update_missing_moods(db_path: str = Query(None)) -> Dict[str, object]:
    """
    Update all songs with NULL mood/intensity values.
    Re-fits model on current data.
    """
    try:
        if db_path is None:
            db_path = get_db_path()
        engine = DBMoodEngine(db_path=db_path, add_debug_cols=True)
        engine.fit(force=True)
        count = engine.update_missing()
        return {
            "status": "success",
            "updated_count": count,
            "message": f"Updated {count} songs with missing moods"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.post("/update-all")
def recompute_all_moods(db_path: str = Query(None)) -> Dict[str, object]:
    """
    Recompute mood predictions for ALL songs.
    This will overwrite existing predictions.
    """
    try:
        if db_path is None:
            db_path = get_db_path()
        engine = DBMoodEngine(db_path=db_path, add_debug_cols=True)
        engine.fit(force=True)
        count = engine.update_all()
        return {
            "status": "success",
            "updated_count": count,
            "message": f"Recomputed moods for {count} songs"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recompute failed: {str(e)}")


@router.get("/moods")
def list_available_moods() -> Dict[str, object]:
    """List all available mood categories."""
    return {
        "moods": MOODS,
        "count": len(MOODS),
        "descriptions": {
            "energetic": "High energy, high happiness (High V, High A)",
            "happy": "Happy, low energy (High V, Low A)",
            "sad": "Sad, low energy (Low V, Low A)",
            "stress": "Stressed, high energy (Low V, High A)",
            "angry": "Angry, high energy + loud (Low V, High A, loud)"
        }
    }


@router.get("/stats")
def get_db_stats(db_path: str = Query(None)) -> Dict[str, object]:
    """Get database statistics."""
    try:
        from backend.src.repo.song_repo import connect, fetch_songs
        if db_path is None:
            db_path = get_db_path()
        con = connect(db_path)
        
        all_songs = fetch_songs(con)
        songs_with_mood = fetch_songs(con, "mood IS NOT NULL")
        
        mood_counts = {}
        for song in songs_with_mood:
            mood = song.get("mood")
            if mood:
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        con.close()
        
        return {
            "total_songs": len(all_songs),
            "songs_with_mood": len(songs_with_mood),
            "songs_without_mood": len(all_songs) - len(songs_with_mood),
            "mood_distribution": mood_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")


# ==================== SEARCH ENDPOINTS ====================

@router.get("/search")
def search_songs(
    query: str = Query(..., min_length=1, description="Search query (title, artist, genre, mood)"),
    top_k: int = Query(10, ge=1, le=50, description="Number of results"),
    db_path: str = Query(None)
) -> List[Dict]:
    """
    Full-text search for songs using TF-IDF.
    
    Args:
        query: Search terms (e.g., "happy pop", "energetic dance")
        top_k: Number of results to return (1-50)
        
    Returns:
        List of matching songs ranked by relevance
    """
    try:
        search_engine = get_search_engine()
        results = search_engine.search(query, top_k=top_k)
        
        # Return songs with relevance scores
        return [
            {**song, "relevance_score": float(score)}
            for song, score in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/by-mood/{mood}")
def search_by_mood(
    mood: str,
    top_k: int = Query(10, ge=1, le=50),
    db_path: str = Query(None)
) -> List[Dict]:
    """Search for songs with specific mood."""
    if mood not in MOODS:
        raise HTTPException(status_code=400, detail=f"Invalid mood. Must be one of: {MOODS}")
    
    try:
        from backend.src.repo.song_repo import connect, fetch_songs
        if db_path is None:
            db_path = get_db_path()
        con = connect(db_path)
        songs = fetch_songs(con, "mood = ?", (mood,))
        con.close()
        return songs[:top_k]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/search/by-genre/{genre}")
def search_by_genre(
    genre: str,
    top_k: int = Query(10, ge=1, le=50),
    db_path: str = Query(None)
) -> List[Dict]:
    """Search for songs with specific genre."""
    try:
        search_engine = get_search_engine()
        results = search_engine.search_by_field("genre", genre, top_k=top_k)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/suggest")
def suggest_songs(
    prefix: str = Query(..., min_length=1, description="Song title or artist prefix"),
    top_k: int = Query(5, ge=1, le=20)
) -> List[str]:
    """
    Get autocomplete suggestions.
    
    Args:
        prefix: Song title or artist prefix (e.g., "Lev" -> "Levitating")
        top_k: Number of suggestions
        
    Returns:
        List of suggestions in format "Title - Artist"
    """
    try:
        search_engine = get_search_engine()
        suggestions = search_engine.suggest(prefix, top_k=top_k)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion failed: {str(e)}")


# ==================== PREFERENCE/RANKING ENDPOINTS ====================

@router.post("/user/{user_id}/preference")
def record_preference(
    user_id: str,
    song_id: int,
    preference: int = Query(..., ge=0, le=1, description="0=dislike, 1=like"),
    db_path: str = Query(None)
) -> Dict[str, object]:
    """
    Record user preference for a song.
    
    Args:
        user_id: Unique user identifier
        song_id: Song ID
        preference: 0 (dislike) or 1 (like)
        
    Returns:
        Feedback recording confirmation and stats
    """
    try:
        from backend.src.repo.song_repo import connect, fetch_song_by_id
        
        # Get song
        if db_path is None:
            db_path = get_db_path()
        con = connect(db_path)
        song = fetch_song_by_id(con, song_id)
        con.close()
        
        if not song:
            raise HTTPException(status_code=404, detail=f"Song {song_id} not found")
        
        # Record preference
        tracker = get_user_tracker(user_id)
        tracker.record_preference(dict(song), preference)
        
        return {
            "status": "recorded",
            "user_id": user_id,
            "song_id": song_id,
            "preference": "liked" if preference == 1 else "disliked",
            "feedback_count": len(tracker.feedback)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record preference: {str(e)}")


@router.post("/user/{user_id}/train")
def train_preference_model(
    user_id: str,
    db_path: str = Query(None)
) -> Dict[str, object]:
    """
    Train preference model from user feedback.
    
    Need at least 3 feedback samples to train.
    """
    try:
        tracker = get_user_tracker(user_id)
        stats = tracker.get_stats()
        
        if stats['total'] < 3:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 3 samples. Got {stats['total']}",
                "stats": stats
            }
        
        tracker.retrain()
        
        return {
            "status": "trained",
            "user_id": user_id,
            "samples_used": stats['total'],
            "model_fitted": tracker.model.is_fitted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/user/{user_id}/predict/{song_id}")
def predict_user_preference(
    user_id: str,
    song_id: int,
    db_path: str = Query(None)
) -> Dict[str, object]:
    """
    Predict if user will like a song.
    
    Returns:
        - prediction: 0 (dislike) or 1 (like)
        - probability_like: Confidence in like prediction (0-1)
    """
    try:
        from backend.src.repo.song_repo import connect, fetch_song_by_id
        
        # Get song
        if db_path is None:
            db_path = get_db_path()
        # Get song
        con = connect(db_path)
        song = fetch_song_by_id(con, song_id)
        con.close()
        
        if not song:
            raise HTTPException(status_code=404, detail=f"Song {song_id} not found")
        
        # Predict
        tracker = get_user_tracker(user_id)
        
        if not tracker.model.is_fitted:
            return {
                "status": "model_not_trained",
                "message": "Train model first with /user/{user_id}/train",
                "song_id": song_id
            }
        
        prediction = tracker.model.predict(dict(song))
        prob_dislike, prob_like = tracker.model.predict_proba(dict(song))
        
        return {
            "user_id": user_id,
            "song_id": song_id,
            "song_title": song.get('title'),
            "prediction": prediction,
            "prediction_label": "will_like" if prediction == 1 else "will_dislike",
            "probability_dislike": float(prob_dislike),
            "probability_like": float(prob_like),
            "confidence": max(float(prob_dislike), float(prob_like))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/user/{user_id}/stats")
def get_user_stats(user_id: str) -> Dict[str, object]:
    """Get user preference statistics."""
    try:
        tracker = get_user_tracker(user_id)
        stats = tracker.get_stats()
        
        return {
            "user_id": user_id,
            "total_feedback": stats['total'],
            "likes": stats['likes'],
            "dislikes": stats['dislikes'],
            "like_ratio": round(stats['like_ratio'], 2),
            "model_trained": tracker.model.is_fitted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")


@router.get("/user/{user_id}/recommend")
def recommend_for_user(
    user_id: str,
    top_k: int = Query(10, ge=1, le=50),
    db_path: str = Query(None)
) -> List[Dict]:
    """
    Get song recommendations for user based on preferences.
    
    Ranks all songs by predicted preference.
    """
    try:
        from backend.src.repo.song_repo import connect, fetch_songs
        
        tracker = get_user_tracker(user_id)
        
        if not tracker.model.is_fitted:
            return {
                "status": "model_not_trained",
                "message": "Train model first with /user/{user_id}/train"
            }
        
        # Get all songs
        if db_path is None:
            db_path = get_db_path()
        con = connect(db_path)
        all_songs = fetch_songs(con)
        con.close()
        
        # Predict preference and score
        recommendations = []
        for song in all_songs:
            _, prob_like = tracker.model.predict_proba(dict(song))
            recommendations.append({
                **song,
                "prediction_score": float(prob_like)
            })
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x['prediction_score'], reverse=True)
        
        return recommendations[:top_k]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


# ==================== HISTORY ENDPOINTS ====================

@router.post("/user/{user_id}/history/{song_id}")
def add_to_history(
    user_id: str,
    song_id: int,
    mood: Optional[str] = Query(None, description="Current mood context"),
    rating: int = Query(0, ge=0, le=5, description="Song rating 1-5"),
    liked: bool = Query(False, description="Whether user liked the song")
) -> Dict[str, object]:
    """
    Record a song play in user's history.
    
    Args:
        user_id: User identifier
        song_id: Song ID
        mood: Optional mood context
        rating: Song rating (0-5, 0 means unrated)
        liked: Whether user liked the song
        
    Returns:
        Recording confirmation with entry ID
    """
    try:
        history_service = get_history_service()
        entry_id = history_service.record_play(
            user_id=int(user_id) if user_id.isdigit() else hash(user_id) % 100000,
            song_id=song_id,
            mood=mood,
            rating=rating,
            liked=liked
        )
        return {
            "status": "recorded",
            "entry_id": entry_id,
            "user_id": user_id,
            "song_id": song_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record history: {str(e)}")


@router.get("/user/{user_id}/history")
def get_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    mood_filter: Optional[str] = Query(None)
) -> List[Dict]:
    """
    Get user's listening history.
    
    Args:
        user_id: User identifier
        limit: Maximum results
        offset: Pagination offset
        mood_filter: Optional mood to filter by
        
    Returns:
        List of history entries with song details
    """
    try:
        history_service = get_history_service()
        return history_service.get_history(
            user_id=int(user_id) if user_id.isdigit() else hash(user_id) % 100000,
            limit=limit,
            offset=offset,
            mood_filter=mood_filter
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/user/{user_id}/liked-songs")
def get_liked_songs(user_id: str) -> List[Dict]:
    """Get all songs user has liked."""
    try:
        history_service = get_history_service()
        return history_service.get_liked_songs(
            user_id=int(user_id) if user_id.isdigit() else hash(user_id) % 100000
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get liked songs: {str(e)}")


@router.get("/user/{user_id}/top-songs")
def get_top_songs(
    user_id: str,
    limit: int = Query(20, ge=1, le=50)
) -> List[Dict]:
    """Get user's most played songs."""
    try:
        history_service = get_history_service()
        return history_service.get_top_songs(
            user_id=int(user_id) if user_id.isdigit() else hash(user_id) % 100000,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top songs: {str(e)}")


@router.put("/user/{user_id}/history/{song_id}/rate")
def rate_song(
    user_id: str,
    song_id: int,
    rating: int = Query(..., ge=1, le=5, description="Rating 1-5")
) -> Dict[str, object]:
    """Set rating for a song in user's history."""
    try:
        history_service = get_history_service()
        success = history_service.rate_song(
            user_id=int(user_id) if user_id.isdigit() else hash(user_id) % 100000,
            song_id=song_id,
            rating=rating
        )
        return {
            "status": "updated" if success else "not_found",
            "song_id": song_id,
            "rating": rating
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rate song: {str(e)}")


@router.put("/user/{user_id}/history/{song_id}/like")
def toggle_like(
    user_id: str,
    song_id: int,
    liked: bool = Query(..., description="Whether to like the song")
) -> Dict[str, object]:
    """Toggle like status for a song."""
    try:
        history_service = get_history_service()
        success = history_service.toggle_like(
            user_id=int(user_id) if user_id.isdigit() else hash(user_id) % 100000,
            song_id=song_id,
            liked=liked
        )
        return {
            "status": "updated" if success else "not_found",
            "song_id": song_id,
            "liked": liked
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle like: {str(e)}")


@router.get("/user/{user_id}/mood-stats")
def get_mood_stats(user_id: str) -> Dict[str, object]:
    """Get mood distribution from user's listening history."""
    try:
        history_service = get_history_service()
        stats = history_service.get_mood_statistics(
            user_id=int(user_id) if user_id.isdigit() else hash(user_id) % 100000
        )
        return {
            "user_id": user_id,
            "mood_distribution": stats,
            "total_plays": sum(stats.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mood stats: {str(e)}")


@router.delete("/user/{user_id}/history/{song_id}")
def remove_from_history(user_id: str, song_id: int) -> Dict[str, object]:
    """Remove a song from user's history."""
    try:
        history_service = get_history_service()
        success = history_service.remove_from_history(
            user_id=int(user_id) if user_id.isdigit() else hash(user_id) % 100000,
            song_id=song_id
        )
        return {
            "status": "deleted" if success else "not_found",
            "song_id": song_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove from history: {str(e)}")


# ==================== PERSONALIZED RANKING ENDPOINTS ====================

@router.post("/user/{user_id}/rank-songs")
def rank_songs_for_user(
    user_id: str,
    song_ids: List[int],
    mood: Optional[str] = Query(None),
    db_path: str = Query(None)
) -> List[Dict]:
    """
    Rank a list of songs personalized for user.
    
    Args:
        user_id: User identifier
        song_ids: List of song IDs to rank
        mood: Optional mood filter
        
    Returns:
        Songs ranked by personalized score
    """
    try:
        from backend.src.repo.song_repo import connect, fetch_songs
        
        if db_path is None:
            db_path = get_db_path()
        con = connect(db_path)
        
        # Fetch songs by IDs
        placeholders = ','.join('?' * len(song_ids))
        songs = fetch_songs(con, f"song_id IN ({placeholders})", tuple(song_ids))
        con.close()
        
        if not songs:
            return []
        
        # Get user tracker and ranking service
        tracker = get_user_tracker(user_id)
        ranking_service = get_ranking_service()
        
        # Update ranking service model if user has trained model
        if tracker.model.is_fitted:
            ranking_service = RankingService(tracker.model)
        
        # Rank songs
        ranked = ranking_service.rank_songs(songs, target_mood=mood)
        
        return ranked
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")


@router.get("/user/{user_id}/personalized-recommend")
def personalized_recommendations(
    user_id: str,
    mood: Optional[str] = Query(None, description="Target mood filter"),
    top_k: int = Query(10, ge=1, le=50),
    diversity: bool = Query(True, description="Enable diversity sampling"),
    db_path: str = Query(None)
) -> List[Dict]:
    """
    Get personalized recommendations with optional mood filter.
    
    Uses trained preference model if available, otherwise returns
    top-rated songs for the mood.
    """
    try:
        from backend.src.repo.song_repo import connect, fetch_songs
        
        if db_path is None:
            db_path = get_db_path()
        con = connect(db_path)
        
        # Get all songs, optionally filtered by mood
        if mood and mood in MOODS:
            songs = fetch_songs(con, "mood = ?", (mood,))
        else:
            songs = fetch_songs(con)
        con.close()
        
        if not songs:
            return []
        
        # Get user tracker
        tracker = get_user_tracker(user_id)
        ranking_service = get_ranking_service()
        
        if tracker.model.is_fitted:
            ranking_service = RankingService(tracker.model)
            recommendations = ranking_service.get_recommendations(
                candidate_songs=songs,
                target_mood=mood,
                top_k=top_k * 2 if diversity else top_k,
                diversify=diversity
            )
        else:
            # Fallback: sort by mood_score
            songs_sorted = sorted(
                songs,
                key=lambda s: float(s.get('mood_score', 0) or 0),
                reverse=True
            )
            recommendations = songs_sorted[:top_k]
        
        return recommendations[:top_k]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


# ==================== TEXT MOOD DETECTION ENDPOINTS ====================

@router.post("/detect-mood-from-text")
def detect_mood_from_text_endpoint(body: TextInput) -> Dict[str, object]:
    """
    Detect mood from user text input.
    Supports Vietnamese and English.
    
    Args:
        body: JSON body with 'text' field containing user message
        
    Returns:
        Detected mood, confidence, matched keywords, intensity
    """
    try:
        from backend.src.pipelines.text_mood_detector import text_mood_detector
        from backend.src.services.constants import MOOD_EMOJI, INTENSITY_EMOJI
        
        result = text_mood_detector.detect(body.text)
        
        return {
            "input_text": body.text,
            "detected_mood": result.mood,
            "confidence": round(result.confidence, 2),
            "keywords_matched": result.keywords_matched,
            "intensity": result.intensity,
            "mood_emoji": MOOD_EMOJI.get(result.mood, "🎵"),
            "intensity_emoji": INTENSITY_EMOJI.get(result.intensity, "✨")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mood detection failed: {str(e)}")


@router.post("/detect-mood-alternatives")
def detect_mood_alternatives_endpoint(body: TextInput, top_k: int = Query(3, ge=1, le=5)) -> Dict[str, object]:
    """
    Detect mood with alternative suggestions.
    
    Args:
        body: JSON body with 'text' field
        top_k: Number of mood alternatives
        
    Returns:
        List of possible moods with confidence scores
    """
    try:
        from backend.src.pipelines.text_mood_detector import text_mood_detector
        from backend.src.services.constants import MOOD_EMOJI
        
        results = text_mood_detector.detect_with_alternatives(body.text, top_k)
        
        return {
            "input_text": body.text,
            "alternatives": [
                {
                    "mood": r.mood,
                    "confidence": round(r.confidence, 2),
                    "keywords": r.keywords_matched,
                    "intensity": r.intensity,
                    "emoji": MOOD_EMOJI.get(r.mood, "🎵")
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/smart-recommend")
def smart_recommend_endpoint(body: SmartRecommendRequest, db_path: str = Query(None)) -> Dict[str, object]:
    """
    Smart recommendation: Detect mood from text and recommend songs.
    
    This endpoint combines text mood detection with song recommendation
    for a seamless user experience.
    
    Args:
        body: JSON body with 'text', optional 'user_id', 'limit'
        
    Returns:
        Detected mood and song recommendations
    """
    try:
        from backend.src.pipelines.text_mood_detector import text_mood_detector
        from backend.src.repo.song_repo import connect, fetch_songs
        from backend.src.services.constants import MOOD_VI_TO_EN, MOOD_EMOJI
        
        text = body.text
        top_k = body.limit
        
        # Step 1: Detect mood from text
        mood_result = text_mood_detector.detect(text)
        detected_mood_vi = mood_result.mood
        
        # Step 2: Convert to English mood for database query
        detected_mood_en = MOOD_VI_TO_EN.get(detected_mood_vi, "happy")
        
        # Step 3: Get songs with matching mood
        if db_path is None:
            db_path = get_db_path()
        con = connect(db_path)
        
        # Try to get songs with exact mood match
        songs = fetch_songs(con, "mood = ?", (detected_mood_en,))
        
        # If no exact match, get all songs and sort by mood_score
        if not songs:
            all_songs = fetch_songs(con)
            songs = sorted(
                all_songs,
                key=lambda s: float(s.get('mood_score', 0) or 0),
                reverse=True
            )
        
        con.close()
        
        # Step 4: Add recommendation reasons
        recommendations = []
        for song in songs[:top_k]:
            reason = _generate_recommendation_reason(
                song, detected_mood_vi, mood_result.intensity
            )
            recommendations.append({
                **song,
                "recommendation_reason": reason
            })
        
        return {
            "input_text": text,
            "detected_mood": {
                "mood": detected_mood_vi,
                "mood_en": detected_mood_en,
                "confidence": round(mood_result.confidence, 2),
                "intensity": mood_result.intensity,
                "keywords": mood_result.keywords_matched,
                "emoji": MOOD_EMOJI.get(detected_mood_vi, "🎵")
            },
            "recommendations": recommendations,
            "total_found": len(songs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart recommend failed: {str(e)}")


def _generate_recommendation_reason(song: Dict, mood: str, intensity: str) -> str:
    """Generate personalized recommendation reason."""
    song_name = song.get('song_name', song.get('name', 'Bài hát'))
    artist = song.get('artist', song.get('artist_name', 'Nghệ sĩ'))
    genre = song.get('genre', 'Pop')
    
    intensity_text = {
        "Nhẹ": "nhẹ nhàng, thư thái",
        "Vừa": "vừa phải, cân bằng",
        "Mạnh": "mạnh mẽ, sôi động"
    }.get(intensity, "phù hợp")
    
    mood_text = {
        "Vui": "vui vẻ, tích cực",
        "Buồn": "sâu lắng, cảm xúc",
        "Suy tư": "trầm ngâm, suy nghĩ",
        "Chill": "thư giãn, bình yên",
        "Năng lượng": "năng lượng, sôi động"
    }.get(mood, "phù hợp")
    
    return (
        f"'{song_name}' của {artist} là lựa chọn hoàn hảo cho tâm trạng {mood_text}. "
        f"Với thể loại {genre} và nhịp điệu {intensity_text}, bài hát này sẽ đem lại "
        f"trải nghiệm âm nhạc tuyệt vời cho bạn."
    )
