"""FastAPI application entry point."""

import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.src.api.mood_api import router as mood_router
from backend.src.api.extended_api import router as extended_router
from backend.src.api.auth_api import router as auth_router
from backend.api.v1 import v1_router  # New production API
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MusicMoodBot API",
    description="""
    Production-level music recommendation chatbot API.
    
    ## Features
    - 🎵 ML-based mood prediction from audio features
    - 💬 Chat-based recommendations with NLP
    - 🔍 Smart search with Vietnamese support
    - 📊 User analytics and insights
    - 🎭 Smooth playlist curation
    - 👤 Personalized recommendations
    - 📋 Playlist management
    
    ## API Versions
    - `/api/v1/` - Production chat API (recommended)
    - `/api/v2/` - Extended analytics API
    - `/api/moods/` - Legacy mood prediction
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
app.include_router(v1_router)  # New production API
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
        "message": "MusicMoodBot API",
        "version": "2.1.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "health": "/health",
        "endpoints": {
            "chat": "/api/v1/chat/message",
            "conversation": "/api/v1/conversation/turn",
            "feedback": "/api/v1/chat/feedback",
            "auth": "/api/v1/auth/login",
            "user": "/api/v1/user/profile",
            "playlist": "/api/v1/playlist",
            "moods": "/api/moods",
            "extended": "/api/v2",
            "playlists": "/api/v2/playlists",
            "analytics": "/api/v2/analytics"
        }
    }


# Server is started via uvicorn when running the application