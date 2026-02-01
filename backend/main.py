"""FastAPI application entry point."""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.src.api.mood_api import router as mood_router
from backend.src.api.extended_api import router as extended_router
from backend.src.api.auth_api import router as auth_router
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Music Mood Prediction API",
    description="""
    ML-powered music mood prediction, search, and personalized recommendations.
    
    ## Features
    - 🎵 Mood prediction from audio features
    - 🔍 Smart search with Vietnamese support
    - 📊 Analytics and insights
    - 🎭 Mood transition planning
    - 📋 Playlist management
    - 🔗 Song similarity
    - ⏰ Time-based recommendations
    - 🌤️ Weather-based recommendations
    - 👤 User preference learning
    - 💾 Export/Import data
    - 🗄️ Database optimization
    """,
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
# Get allowed origins from environment variable or use defaults
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000").split(",")
# For development, allow all origins
if os.getenv("ALLOW_ALL_ORIGINS", "true").lower() == "true":
    CORS_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(mood_router, prefix="/api/moods", tags=["moods"])
app.include_router(extended_router, prefix="/api/v2", tags=["extended", "playlists", "analytics"])
app.include_router(auth_router, prefix="/api/v2", tags=["authentication"])


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Music Mood Prediction API",
        "version": "2.1.0"
    }


@app.get("/")
def root():
    """Root endpoint - redirects to API docs."""
    return {
        "message": "Music Mood Prediction API",
        "version": "2.1.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "health": "/health",
        "endpoints": {
            "moods": "/api/moods",
            "extended": "/api/v2",
            "playlists": "/api/v2/playlists",
            "analytics": "/api/v2/analytics",
            "similarity": "/api/v2/songs/{id}/similar",
            "time_recommendations": "/api/v2/recommendations/now",
            "user_preferences": "/api/v2/users/{id}/preferences",
            "export": "/api/v2/export/songs",
            "backup": "/api/v2/backup/create"
        }
    }


# Server is started via uvicorn when running the application