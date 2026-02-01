"""
Mood Routes
===========
Endpoints for mood prediction and analysis.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter()

# Lazy imports to avoid circular dependencies
_engine = None


def get_engine():
    """Lazy load mood engine"""
    global _engine
    if _engine is None:
        from backend.src.services.mood_services import DBMoodEngine
        import os
        db_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "src", "database", "music.db"
        )
        _engine = DBMoodEngine(db_path=db_path, add_debug_cols=True, auto_fit=True)
        _engine.fit(force=True)
    return _engine


class SongInput(BaseModel):
    """Input for mood prediction"""
    energy: float = 50
    valence: float = 50
    tempo: float = 120
    loudness: float = -10
    danceability: float = 50
    acousticness: float = 50
    genre: Optional[str] = None


@router.get("/")
def list_moods():
    """List all available mood categories"""
    from shared.constants import MOODS, MOOD_DESCRIPTIONS_EN
    return {
        "moods": MOODS,
        "count": len(MOODS),
        "descriptions": MOOD_DESCRIPTIONS_EN
    }


@router.post("/predict")
def predict_mood(song: SongInput):
    """Predict mood for a song based on audio features"""
    try:
        engine = get_engine()
        result = engine.predict_one(song.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/stats")
def get_mood_stats():
    """Get mood distribution statistics"""
    try:
        from backend.repositories import SongRepository
        repo = SongRepository()
        songs = repo.get_all(limit=10000)
        
        mood_counts = {}
        for song in songs:
            mood = song.get("mood")
            if mood:
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        return {
            "total_songs": len(songs),
            "mood_distribution": mood_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")


@router.post("/update-missing")
def update_missing_moods():
    """Update songs with missing mood predictions"""
    try:
        engine = get_engine()
        engine.fit(force=True)
        count = engine.update_missing()
        return {
            "status": "success",
            "updated_count": count,
            "message": f"Updated {count} songs with missing moods"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
