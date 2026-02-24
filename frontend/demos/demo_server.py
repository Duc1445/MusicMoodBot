#!/usr/bin/env python
"""
Music Mood Prediction - Simple Demo Server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Music Mood Prediction API",
    description="ML-powered music mood prediction, search, and personalized recommendations",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo data
sample_songs = [
    {"id": 1, "title": "Happily", "artist": "One Direction", "mood": "happy"},
    {"id": 2, "title": "Levitating", "artist": "Dua Lipa", "mood": "upbeat"},
    {"id": 3, "title": "Someone Like You", "artist": "Adele", "mood": "sad"},
    {"id": 4, "title": "Bohemian Rhapsody", "artist": "Queen", "mood": "epic"},
    {"id": 5, "title": "Chasing Cars", "artist": "Snow Patrol", "mood": "calm"},
]

@app.get("/")
def read_root():
    return {
        "message": "🎵 Welcome to Music Mood Prediction API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }

@app.get("/api/songs")
def get_songs():
    """Get all available songs"""
    return {
        "songs": sample_songs,
        "count": len(sample_songs)
    }

@app.get("/api/songs/{song_id}")
def get_song(song_id: int):
    """Get a specific song by ID"""
    for song in sample_songs:
        if song["id"] == song_id:
            return song
    return {"error": "Song not found"}

@app.get("/api/recommendations")
def get_recommendations(mood: str = "happy", limit: int = 5):
    """Get song recommendations by mood"""
    recommendations = [s for s in sample_songs if s["mood"].lower() == mood.lower()]
    return {
        "mood": mood,
        "recommendations": recommendations[:limit],
        "count": len(recommendations[:limit])
    }

@app.post("/api/predict_mood")
def predict_mood(text: dict):
    """Predict mood from text"""
    user_text = text.get("text", "").lower()
    
    # Simple mood detection
    if any(word in user_text for word in ["happy", "great", "amazing", "love", "awesome"]):
        mood = "happy"
    elif any(word in user_text for word in ["sad", "depressed", "lonely", "hurt", "cry"]):
        mood = "sad"
    elif any(word in user_text for word in ["calm", "relax", "peace", "quiet", "chill"]):
        mood = "calm"
    else:
        mood = "upbeat"
    
    return {
        "text": text.get("text"),
        "predicted_mood": mood,
        "confidence": 0.85
    }

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎵 Music Mood Prediction - Backend Server (DEMO)")
    print("="*70 + "\n")
    print("✅ Starting FastAPI server...")
    print("📍 API URL: http://localhost:8000")
    print("📚 Swagger Docs: http://localhost:8000/api/docs")
    print("🔍 ReDoc: http://localhost:8000/api/redoc")
    print("\n" + "-"*70)
    print("Press Ctrl+C to stop server\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
