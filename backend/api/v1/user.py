"""
User Profile API Router
=======================
Endpoints for user profile management.

Endpoints:
- GET /user/profile - Get user profile with stats
- PUT /user/profile - Update user profile
- GET /user/history - Get listening history
- GET /user/preferences - Get learned preferences
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import json

from backend.repositories import (
    UserRepository,
    HistoryRepository,
    FeedbackRepository,
    UserPreferencesRepository
)
from backend.api.v1.dependencies import get_current_user_id

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ProfileUpdateRequest(BaseModel):
    """Request to update user profile."""
    favorite_mood: Optional[str] = None
    favorite_genres: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "favorite_mood": "Chill",
                "favorite_genres": ["V-Pop", "Indie", "R&B"]
            }
        }


class UserStats(BaseModel):
    """User listening statistics."""
    total_songs_listened: int
    total_likes: int
    total_dislikes: int
    favorite_mood: Optional[str]
    favorite_genres: List[str]
    favorite_artists: List[str]


class PreferenceWeight(BaseModel):
    """Learned preference weight."""
    value: str
    weight: float
    interaction_count: int


class UserPreferences(BaseModel):
    """All learned user preferences."""
    mood_weights: Dict[str, float]
    genre_weights: Dict[str, float]
    artist_weights: Dict[str, float]


class UserProfileResponse(BaseModel):
    """Full user profile with stats and preferences."""
    user_id: int
    username: str
    email: str
    created_at: str
    avatar_url: Optional[str]
    stats: UserStats
    preferences: UserPreferences


class HistoryItem(BaseModel):
    """A single history entry."""
    history_id: int
    song_id: int
    song_name: str
    artist: str
    genre: str
    mood: str
    intensity: Optional[str]
    listened_at: str
    feedback: Optional[str]


class HistoryResponse(BaseModel):
    """Paginated history response."""
    status: str
    total: int
    items: List[HistoryItem]
    pagination: dict


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(user_id: int = Depends(get_current_user_id)):
    """
    Get user profile with statistics and learned preferences.
    
    Returns:
    - Basic user info
    - Listening statistics (total songs, likes, etc.)
    - Favorite mood/genres/artists
    - Learned preference weights
    """
    user_repo = UserRepository()
    history_repo = HistoryRepository()
    feedback_repo = FeedbackRepository()
    prefs_repo = UserPreferencesRepository()
    
    # Get user
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get stats
    history = history_repo.get_user_history(user_id, limit=1000)
    user_feedback = feedback_repo.get_user_feedback(user_id, limit=1000)
    
    likes = [f for f in user_feedback if f['feedback_type'] == 'like']
    dislikes = [f for f in user_feedback if f['feedback_type'] == 'dislike']
    
    # Get learned preferences
    pref_summary = prefs_repo.get_preference_summary(user_id)
    all_prefs = prefs_repo.get_user_preferences(user_id)
    
    # Parse stored favorite_genres
    stored_genres = user.get('favorite_genres')
    if isinstance(stored_genres, str):
        try:
            stored_genres = json.loads(stored_genres)
        except:
            stored_genres = []
    
    # Combine stored and learned favorites
    favorite_genres = stored_genres or pref_summary.get('favorite_genres', [])
    favorite_artists = pref_summary.get('favorite_artists', [])
    
    stats = UserStats(
        total_songs_listened=len(history),
        total_likes=len(likes),
        total_dislikes=len(dislikes),
        favorite_mood=user.get('favorite_mood') or (pref_summary.get('favorite_moods', [None])[0]),
        favorite_genres=favorite_genres[:5],
        favorite_artists=favorite_artists[:5]
    )
    
    preferences = UserPreferences(
        mood_weights=all_prefs.get('mood', {}),
        genre_weights=all_prefs.get('genre', {}),
        artist_weights=all_prefs.get('artist', {})
    )
    
    return UserProfileResponse(
        user_id=user['user_id'],
        username=user['username'],
        email=user['email'],
        created_at=str(user.get('created_at', '')),
        avatar_url=user.get('avatar_url'),
        stats=stats,
        preferences=preferences
    )


@router.put("/profile")
async def update_profile(
    request: ProfileUpdateRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Update user profile settings.
    
    Updatable fields:
    - favorite_mood
    - favorite_genres
    - avatar_url
    """
    user_repo = UserRepository()
    
    # Build update fields
    update_fields = {}
    
    if request.favorite_mood is not None:
        update_fields['favorite_mood'] = request.favorite_mood
    
    if request.favorite_genres is not None:
        update_fields['favorite_genres'] = json.dumps(request.favorite_genres)
    
    if request.avatar_url is not None:
        update_fields['avatar_url'] = request.avatar_url
    
    if not update_fields:
        return {"status": "success", "message": "Không có gì để cập nhật"}
    
    # Update in database
    from backend.repositories.connection import get_connection
    
    with get_connection() as conn:
        set_clause = ", ".join(f"{k} = ?" for k in update_fields)
        values = list(update_fields.values()) + [user_id]
        conn.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
        conn.commit()
    
    return {"status": "success", "message": "Đã cập nhật thông tin"}


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    user_id: int = Depends(get_current_user_id),
    mood: Optional[str] = Query(None, description="Filter by mood"),
    from_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get user's listening history with optional filters.
    
    **Filters:**
    - `mood`: Filter by mood (Vui, Buồn, etc.)
    - `from_date` / `to_date`: Date range filter
    
    **Pagination:**
    - `limit`: Max items per page (default 20, max 100)
    - `offset`: Skip items for pagination
    """
    history_repo = HistoryRepository()
    feedback_repo = FeedbackRepository()
    
    # Get history
    history = history_repo.get_user_history(user_id, limit=500)
    
    # Get user feedback for each song
    user_feedback = {f['song_id']: f['feedback_type'] 
                     for f in feedback_repo.get_user_feedback(user_id)}
    
    # Apply filters
    if mood:
        history = [h for h in history if h.get('mood') == mood]
    
    if from_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            history = [h for h in history 
                      if datetime.fromisoformat(str(h.get('timestamp', ''))) >= from_dt]
        except:
            pass
    
    if to_date:
        try:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")
            history = [h for h in history 
                      if datetime.fromisoformat(str(h.get('timestamp', ''))) <= to_dt]
        except:
            pass
    
    # Paginate
    total = len(history)
    history = history[offset:offset + limit]
    
    # Format response
    items = []
    for h in history:
        items.append(HistoryItem(
            history_id=h.get('history_id', 0),
            song_id=h.get('song_id', 0),
            song_name=h.get('song_name') or h.get('name', 'Unknown'),
            artist=h.get('artist', 'Unknown'),
            genre=h.get('genre', ''),
            mood=h.get('mood', ''),
            intensity=h.get('intensity'),
            listened_at=str(h.get('timestamp', '')),
            feedback=user_feedback.get(h.get('song_id'))
        ))
    
    return HistoryResponse(
        status="success",
        total=total,
        items=items,
        pagination={
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    )


@router.get("/preferences")
async def get_preferences(user_id: int = Depends(get_current_user_id)):
    """
    Get detailed learned preferences.
    
    Shows weights for:
    - Moods
    - Genres
    - Artists
    
    Higher weight = stronger preference.
    """
    prefs_repo = UserPreferencesRepository()
    
    all_prefs = prefs_repo.get_user_preferences(user_id)
    
    # Get top items for each category
    top_moods = prefs_repo.get_top_preferences(user_id, "mood", limit=10)
    top_genres = prefs_repo.get_top_preferences(user_id, "genre", limit=10)
    top_artists = prefs_repo.get_top_preferences(user_id, "artist", limit=10)
    
    return {
        "status": "success",
        "preferences": {
            "mood": {
                "weights": all_prefs.get('mood', {}),
                "top": [item['preference_value'] for item in top_moods]
            },
            "genre": {
                "weights": all_prefs.get('genre', {}),
                "top": [item['preference_value'] for item in top_genres]
            },
            "artist": {
                "weights": all_prefs.get('artist', {}),
                "top": [item['preference_value'] for item in top_artists]
            }
        }
    }


@router.delete("/history")
async def clear_history(user_id: int = Depends(get_current_user_id)):
    """
    Clear all listening history for the user.
    
    **Warning:** This action cannot be undone.
    """
    history_repo = HistoryRepository()
    
    deleted = history_repo.clear_user_history(user_id)
    
    return {
        "status": "success",
        "message": f"Đã xóa {deleted} bản ghi lịch sử"
    }


@router.delete("/preferences")
async def reset_preferences(user_id: int = Depends(get_current_user_id)):
    """
    Reset all learned preferences.
    
    This will reset personalization - recommendations will start fresh.
    """
    prefs_repo = UserPreferencesRepository()
    
    deleted = prefs_repo.reset_user_preferences(user_id)
    
    return {
        "status": "success",
        "message": f"Đã reset {deleted} preference weights"
    }
