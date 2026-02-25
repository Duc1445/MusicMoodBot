"""
Playlist API Router
===================
Endpoints for playlist management.

Endpoints:
- GET /playlist - List user's playlists
- POST /playlist - Create new playlist
- GET /playlist/{id} - Get playlist with songs
- PUT /playlist/{id} - Update playlist
- DELETE /playlist/{id} - Delete playlist
- POST /playlist/{id}/songs - Add songs to playlist
- DELETE /playlist/{id}/songs/{song_id} - Remove song from playlist
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from backend.repositories import PlaylistRepository, SongRepository
from backend.api.v1.dependencies import get_current_user_id

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CreatePlaylistRequest(BaseModel):
    """Request to create a new playlist."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    mood: Optional[str] = None
    song_ids: Optional[List[int]] = Field(None, description="Initial songs to add")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Chill Evening",
                "description": "Relaxing songs for evening",
                "mood": "Chill",
                "song_ids": [1, 5, 12, 23]
            }
        }


class UpdatePlaylistRequest(BaseModel):
    """Request to update playlist metadata."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    mood: Optional[str] = None


class AddSongsRequest(BaseModel):
    """Request to add songs to playlist."""
    song_ids: List[int] = Field(..., min_items=1)


class ReorderSongsRequest(BaseModel):
    """Request to reorder songs in playlist."""
    song_order: List[int] = Field(..., description="Song IDs in new order")


class PlaylistSong(BaseModel):
    """Song in a playlist."""
    position: int
    song_id: int
    name: str
    artist: str
    genre: str
    mood: Optional[str]
    added_at: str


class PlaylistResponse(BaseModel):
    """Response with playlist details."""
    playlist_id: int
    name: str
    description: Optional[str]
    mood: Optional[str]
    song_count: int
    total_duration_minutes: int
    created_at: str
    updated_at: str
    is_auto_generated: bool


class PlaylistWithSongsResponse(BaseModel):
    """Response with playlist and all songs."""
    playlist_id: int
    name: str
    description: Optional[str]
    mood: Optional[str]
    song_count: int
    created_at: str
    is_auto_generated: bool
    songs: List[PlaylistSong]


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/", response_model=List[PlaylistResponse])
async def list_playlists(
    user_id: int = Depends(get_current_user_id),
    include_auto: bool = Query(True, description="Include auto-generated playlists")
):
    """
    Get all playlists for the current user.
    
    Set `include_auto=false` to exclude auto-generated chat playlists.
    """
    playlist_repo = PlaylistRepository()
    
    playlists = playlist_repo.get_user_playlists(user_id, include_auto=include_auto)
    
    return [
        PlaylistResponse(
            playlist_id=p['playlist_id'],
            name=p['name'],
            description=p.get('description'),
            mood=p.get('mood'),
            song_count=p.get('song_count', 0),
            total_duration_minutes=p.get('total_duration_seconds', 0) // 60,
            created_at=str(p.get('created_at', '')),
            updated_at=str(p.get('updated_at', '')),
            is_auto_generated=bool(p.get('is_auto_generated', False))
        )
        for p in playlists
    ]


@router.post("/", response_model=dict)
async def create_playlist(
    request: CreatePlaylistRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Create a new playlist.
    
    Optionally provide `song_ids` to add initial songs.
    """
    playlist_repo = PlaylistRepository()
    
    # Create playlist
    playlist_id = playlist_repo.create(
        user_id=user_id,
        name=request.name,
        description=request.description,
        mood=request.mood,
        is_auto_generated=False
    )
    
    if not playlist_id:
        raise HTTPException(status_code=500, detail="Failed to create playlist")
    
    # Add initial songs if provided
    if request.song_ids:
        playlist_repo.add_songs_bulk(playlist_id, request.song_ids)
    
    return {
        "status": "success",
        "playlist_id": playlist_id,
        "message": "Playlist đã được tạo"
    }


@router.get("/{playlist_id}", response_model=PlaylistWithSongsResponse)
async def get_playlist(
    playlist_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Get a playlist with all its songs.
    """
    playlist_repo = PlaylistRepository()
    
    playlist = playlist_repo.get_playlist_with_songs(playlist_id)
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Verify ownership
    if playlist['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this playlist")
    
    songs = [
        PlaylistSong(
            position=s.get('position', 0),
            song_id=s['song_id'],
            name=s.get('name', 'Unknown'),
            artist=s.get('artist', 'Unknown'),
            genre=s.get('genre', ''),
            mood=s.get('mood'),
            added_at=str(s.get('added_at', ''))
        )
        for s in playlist.get('songs', [])
    ]
    
    return PlaylistWithSongsResponse(
        playlist_id=playlist['playlist_id'],
        name=playlist['name'],
        description=playlist.get('description'),
        mood=playlist.get('mood'),
        song_count=len(songs),
        created_at=str(playlist.get('created_at', '')),
        is_auto_generated=bool(playlist.get('is_auto_generated', False)),
        songs=songs
    )


@router.put("/{playlist_id}")
async def update_playlist(
    playlist_id: int,
    request: UpdatePlaylistRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Update playlist metadata (name, description, mood).
    """
    playlist_repo = PlaylistRepository()
    
    # Verify ownership
    playlist = playlist_repo.get_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if playlist['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Build update fields
    update_fields = {}
    if request.name is not None:
        update_fields['name'] = request.name
    if request.description is not None:
        update_fields['description'] = request.description
    if request.mood is not None:
        update_fields['mood'] = request.mood
    
    if update_fields:
        playlist_repo.update_playlist(playlist_id, **update_fields)
    
    return {"status": "success", "message": "Playlist đã được cập nhật"}


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Delete a playlist and all its songs.
    """
    playlist_repo = PlaylistRepository()
    
    # Verify ownership
    playlist = playlist_repo.get_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if playlist['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = playlist_repo.delete_playlist(playlist_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete playlist")
    
    return {"status": "success", "message": "Playlist đã được xóa"}


@router.post("/{playlist_id}/songs")
async def add_songs(
    playlist_id: int,
    request: AddSongsRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Add songs to a playlist.
    """
    playlist_repo = PlaylistRepository()
    song_repo = SongRepository()
    
    # Verify ownership
    playlist = playlist_repo.get_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if playlist['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify all songs exist
    for song_id in request.song_ids:
        if not song_repo.exists(song_id):
            raise HTTPException(
                status_code=400, 
                detail=f"Song ID {song_id} not found"
            )
    
    # Add songs
    added = playlist_repo.add_songs_bulk(playlist_id, request.song_ids)
    
    return {
        "status": "success",
        "message": f"Đã thêm {added} bài hát",
        "added_count": added
    }


@router.delete("/{playlist_id}/songs/{song_id}")
async def remove_song(
    playlist_id: int,
    song_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Remove a song from a playlist.
    """
    playlist_repo = PlaylistRepository()
    
    # Verify ownership
    playlist = playlist_repo.get_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if playlist['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = playlist_repo.remove_song(playlist_id, song_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Song not in playlist")
    
    return {"status": "success", "message": "Đã xóa bài hát khỏi playlist"}


@router.put("/{playlist_id}/reorder")
async def reorder_songs(
    playlist_id: int,
    request: ReorderSongsRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Reorder songs in a playlist.
    
    Provide all song IDs in the desired order.
    """
    playlist_repo = PlaylistRepository()
    
    # Verify ownership
    playlist = playlist_repo.get_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if playlist['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = playlist_repo.reorder_songs(playlist_id, request.song_order)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reorder")
    
    return {"status": "success", "message": "Đã sắp xếp lại playlist"}
