"""FastAPI routes for mood prediction, search, and ranking."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional, Tuple
import os

from backend.src.services.mood_services import DBMoodEngine
from backend.src.services.constants import MOODS, Song
from backend.src.search.tfidf_search import TFIDFSearchEngine, create_search_engine
from backend.src.ranking.preference_model import PreferenceModel, UserPreferenceTracker

router = APIRouter()

# Initialize components globally
_engine: Optional[DBMoodEngine] = None
_search_engine: Optional[TFIDFSearchEngine] = None
_user_trackers: Dict[str, UserPreferenceTracker] = {}


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
def list_available_moods() -> Dict[str, List[str]]:
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


