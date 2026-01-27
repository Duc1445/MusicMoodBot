"""FastAPI application entry point."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.src.api.mood_api import router as mood_router
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

# Include routers
app.include_router(mood_router, prefix="/api/moods", tags=["moods"])


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Music Mood Prediction API",
        "version": "1.0.0"
    }


@app.get("/")
def root():
    """Root endpoint - redirects to API docs."""
    return {
        "message": "Music Mood Prediction API",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )