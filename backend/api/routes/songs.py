"""
Song Routes
===========
CRUD endpoints for songs.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter()


class SongCreate(BaseModel):
    """Create song request"""
    name: str
    artist: str
    genre: Optional[str] = None
    suy_score: Optional[float] = None
    reason: Optional[str] = None
    moods: Optional[str] = None


@router.get("/")
def list_songs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List all songs with pagination"""
    try:
        from backend.repositories import SongRepository
        repo = SongRepository()
        songs = repo.get_all(limit=limit, offset=offset)
        return {
            "songs": songs,
            "count": len(songs),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-mood/{mood}")
def get_songs_by_mood(
    mood: str,
    limit: int = Query(20, ge=1, le=100)
):
    """Get songs filtered by mood"""
    from shared.constants import MOODS
    if mood not in MOODS:
        raise HTTPException(status_code=400, detail=f"Invalid mood. Must be one of: {MOODS}")
    
    try:
        from backend.repositories import SongRepository
        repo = SongRepository()
        songs = repo.get_by_mood(mood, limit=limit)
        return songs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-artist/{artist}")
def get_songs_by_artist(
    artist: str,
    limit: int = Query(20, ge=1, le=100)
):
    """Get songs by artist (partial match)"""
    try:
        from backend.repositories import SongRepository
        repo = SongRepository()
        songs = repo.get_by_artist(artist, limit=limit)
        return songs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-genre/{genre}")
def get_songs_by_genre(
    genre: str,
    limit: int = Query(20, ge=1, le=100)
):
    """Get songs by genre"""
    try:
        from backend.repositories import SongRepository
        repo = SongRepository()
        songs = repo.get_by_genre(genre, limit=limit)
        return songs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/random")
def get_random_songs(
    limit: int = Query(5, ge=1, le=20),
    mood: Optional[str] = None
):
    """Get random songs, optionally filtered by mood"""
    try:
        from backend.repositories import SongRepository
        repo = SongRepository()
        songs = repo.get_random(limit=limit, mood=mood)
        return songs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{song_id}")
def get_song(song_id: int):
    """Get a specific song by ID"""
    try:
        from backend.repositories import SongRepository
        repo = SongRepository()
        song = repo.get_by_id(song_id)
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        return song
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
def create_song(song: SongCreate):
    """Create a new song"""
    try:
        from backend.repositories import SongRepository
        repo = SongRepository()
        song_id = repo.add(**song.model_dump())
        if song_id:
            return {"song_id": song_id, "status": "created"}
        raise HTTPException(status_code=500, detail="Failed to create song")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
