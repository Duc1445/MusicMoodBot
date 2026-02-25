"""
API v1 Package
==============
RESTful API endpoints for MusicMoodBot.

Routes:
- /api/v1/auth - Authentication
- /api/v1/chat - Chat & recommendations
- /api/v1/user - User profile
- /api/v1/playlist - Playlist management
- /api/v1/conversation - Multi-turn conversation
- /api/v1/recommend - Advanced recommendations (v4.0)
- /api/v1/metrics - System metrics & experiments (v4.0)
- /api/v1/learning - Adaptive learning controls (v4.0)
- /api/v1/v5 - Adaptive recommendations v5.0
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .chat import router as chat_router
from .user import router as user_router
from .playlist import router as playlist_router
from .conversation import router as conversation_router
from .analytics import router as analytics_router
from .recommendation import router as recommendation_router
from .adaptive import router as adaptive_router

# Create main v1 router
v1_router = APIRouter(prefix="/api/v1")

# Include sub-routers
v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
v1_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
v1_router.include_router(user_router, prefix="/user", tags=["User"])
v1_router.include_router(playlist_router, prefix="/playlist", tags=["Playlist"])
v1_router.include_router(conversation_router, prefix="/conversation", tags=["Conversation"])
v1_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])

# Advanced Recommendation System v4.0
v1_router.include_router(recommendation_router, prefix="/recommend", tags=["Recommendations"])
v1_router.include_router(recommendation_router, prefix="/metrics", tags=["Metrics"])
v1_router.include_router(recommendation_router, prefix="/learning", tags=["Learning"])

# Adaptive Recommendation System v5.0
v1_router.include_router(adaptive_router, prefix="/v5", tags=["Adaptive v5.0"])

__all__ = ["v1_router"]
