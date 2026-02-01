"""
API Routes Package
==================
Split routes by domain for maintainability.

Usage:
    from backend.api.routes import api_router
    app.include_router(api_router)
"""

from fastapi import APIRouter

# Import all route modules
from . import health
from . import songs
from . import moods
from . import search
from . import recommendations

# Create main API router
api_router = APIRouter(prefix="/api")

# Include all sub-routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(moods.router, prefix="/moods", tags=["Moods"])
api_router.include_router(songs.router, prefix="/songs", tags=["Songs"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])

__all__ = ["api_router"]
