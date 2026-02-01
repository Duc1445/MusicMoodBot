"""
Recommendation Routes
=====================
Smart recommendation and text-based mood detection.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter()


class TextInput(BaseModel):
    """Text input for mood detection"""
    text: str


class SmartRecommendRequest(BaseModel):
    """Smart recommendation request"""
    text: str
    user_id: Optional[str] = None
    limit: int = 10


@router.post("/detect-mood")
def detect_mood_from_text(input: TextInput):
    """Detect mood from user text using NLP"""
    try:
        from backend.src.pipelines.text_mood_detector import text_mood_detector
        result = text_mood_detector.detect(input.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/smart")
def smart_recommend(request: SmartRecommendRequest):
    """
    Smart recommendation based on text input.
    Analyzes mood from text and returns matching songs.
    """
    try:
        from backend.src.pipelines.text_mood_detector import text_mood_detector
        from backend.repositories import SongRepository
        
        # Detect mood from text
        detection = text_mood_detector.detect(request.text)
        mood = detection.get("mood", "happy")
        intensity = detection.get("intensity", "medium")
        
        # Get songs matching mood
        repo = SongRepository()
        songs = repo.get_by_mood(mood, limit=request.limit)
        
        return {
            "detected_mood": mood,
            "detected_intensity": intensity,
            "confidence": detection.get("confidence", 0.5),
            "songs": songs,
            "explanation": detection.get("explanation", f"Detected {mood} mood from your message")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@router.post("/by-mood")
def recommend_by_mood(
    mood: str = Query(..., description="Mood category"),
    intensity: str = Query("medium", description="Intensity level"),
    limit: int = Query(10, ge=1, le=50)
):
    """Recommend songs by specified mood and intensity"""
    from shared.constants import MOODS
    if mood not in MOODS:
        raise HTTPException(status_code=400, detail=f"Invalid mood. Must be one of: {MOODS}")
    
    try:
        from backend.repositories import SongRepository
        repo = SongRepository()
        songs = repo.get_by_mood(mood, limit=limit)
        return {
            "mood": mood,
            "intensity": intensity,
            "songs": songs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{song_id}")
def get_similar_songs(
    song_id: int,
    limit: int = Query(5, ge=1, le=20)
):
    """Get songs similar to a given song"""
    try:
        from backend.src.pipelines.song_similarity import get_similarity_engine
        from backend.repositories import SongRepository
        
        repo = SongRepository()
        song = repo.get_by_id(song_id)
        
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        engine = get_similarity_engine()
        similar = engine.find_similar(song, limit=limit)
        
        return {
            "source_song": song,
            "similar_songs": similar
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
