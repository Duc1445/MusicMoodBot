"""
API Dependencies
================
Shared dependencies for API routes (authentication, rate limiting, etc.)
"""

from fastapi import HTTPException, Header, Depends
from typing import Optional
import jwt
import os

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "musicmoodbot-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


async def get_current_user_id(
    authorization: Optional[str] = Header(None)
) -> int:
    """
    Extract user_id from JWT token in Authorization header.
    
    For development, allows anonymous access with user_id=1.
    In production, enforce valid JWT.
    """
    # For development: allow anonymous access
    if not authorization:
        # Return demo user
        return 1
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        # Decode JWT
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        return int(user_id)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")


async def get_optional_user_id(
    authorization: Optional[str] = Header(None)
) -> Optional[int]:
    """
    Extract user_id if token provided, otherwise return None.
    For endpoints that work for both authenticated and anonymous users.
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user_id(authorization)
    except HTTPException:
        return None


def get_db_path() -> str:
    """
    Get the database path for analytics and other DB operations.
    
    Returns the path to the SQLite database file.
    """
    # Check environment variable first
    db_path = os.environ.get("MUSICMOODBOT_DB_PATH")
    if db_path:
        return db_path
    
    # Default to project root database
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    return os.path.join(project_root, "mmbot.db")
