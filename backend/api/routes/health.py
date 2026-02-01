"""
Health Check Routes
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "musicmoodbot"}


@router.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "MusicMoodBot API",
        "version": "2.0.0",
        "docs": "/docs"
    }
