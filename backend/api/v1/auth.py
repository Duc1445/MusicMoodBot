"""
Authentication API Router
=========================
Endpoints for user authentication.

Endpoints:
- POST /auth/register - Register new user
- POST /auth/login - Login and get tokens
- POST /auth/refresh - Refresh access token
- GET /auth/me - Get current user info
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timedelta
import jwt
import hashlib
import secrets
import os
import re

from backend.repositories import UserRepository
from backend.api.v1.dependencies import get_current_user_id

router = APIRouter()

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "musicmoodbot-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RegisterRequest(BaseModel):
    """Request body for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "musicfan123",
                "email": "fan@email.com",
                "password": "securePass123"
            }
        }


class LoginRequest(BaseModel):
    """Request body for login."""
    email: str = Field(..., description="Email or username")
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "fan@email.com",
                "password": "securePass123"
            }
        }


class TokenResponse(BaseModel):
    """Response with JWT tokens."""
    status: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str


class UserResponse(BaseModel):
    """Response with user info."""
    user_id: int
    username: str
    email: str
    created_at: str
    favorite_mood: Optional[str]
    favorite_genres: Optional[list]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def hash_password(password: str, salt: str = None) -> tuple:
    """Hash password with salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    salted = f"{password}{salt}"
    hashed = hashlib.sha256(salted.encode('utf-8')).hexdigest()
    return hashed, salt


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash (hash contains salt)."""
    # Hash format: "hash:salt"
    try:
        stored, salt = stored_hash.rsplit(":", 1)
        computed, _ = hash_password(password, salt)
        return secrets.compare_digest(computed, stored)
    except ValueError:
        # Old format without salt - direct compare
        computed, _ = hash_password(password, "")
        return secrets.compare_digest(computed, stored_hash)


def create_tokens(user_id: int, username: str) -> tuple:
    """Create access and refresh tokens."""
    now = datetime.utcnow()
    
    # Access token
    access_payload = {
        "user_id": user_id,
        "username": username,
        "type": "access",
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now
    }
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # Refresh token
    refresh_payload = {
        "user_id": user_id,
        "type": "refresh",
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": now
    }
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return access_token, refresh_token


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/register")
async def register(request: RegisterRequest):
    """
    Register a new user account.
    
    **Requirements:**
    - Username: 3-50 characters, unique
    - Email: Valid email format, unique
    - Password: Minimum 6 characters
    """
    user_repo = UserRepository()
    
    # Check if username exists
    if user_repo.username_exists(request.username):
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    
    # Check if email exists
    if user_repo.email_exists(request.email):
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")
    
    # Hash password
    password_hash, salt = hash_password(request.password)
    stored_hash = f"{password_hash}:{salt}"
    
    # Create user
    user_id = user_repo.add(
        username=request.username,
        email=request.email,
        password_hash=stored_hash
    )
    
    if not user_id:
        raise HTTPException(status_code=500, detail="Không thể tạo tài khoản")
    
    return {
        "status": "success",
        "user_id": user_id,
        "message": "Đăng ký thành công! Vui lòng đăng nhập."
    }


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login with email/username and password.
    
    Returns JWT access token and refresh token.
    """
    user_repo = UserRepository()
    
    # Find user by email or username
    user = user_repo.get_by_identifier(request.email)
    
    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    
    # Verify password
    if not verify_password(request.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    
    # Create tokens
    access_token, refresh_token = create_tokens(user['user_id'], user['username'])
    
    # Parse favorite_genres from JSON if needed
    favorite_genres = user.get('favorite_genres')
    if isinstance(favorite_genres, str):
        import json
        try:
            favorite_genres = json.loads(favorite_genres)
        except:
            favorite_genres = []
    
    return TokenResponse(
        status="success",
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "user_id": user['user_id'],
            "username": user['username'],
            "email": user['email'],
            "favorite_mood": user.get('favorite_mood'),
            "favorite_genres": favorite_genres or []
        }
    )


@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    try:
        payload = jwt.decode(request.refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("user_id")
        
        # Get user info
        user_repo = UserRepository()
        user = user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Create new tokens
        access_token, new_refresh_token = create_tokens(user['user_id'], user['username'])
        
        return {
            "status": "success",
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: int = Depends(get_current_user_id)):
    """
    Get current authenticated user's information.
    """
    user_repo = UserRepository()
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Parse favorite_genres
    favorite_genres = user.get('favorite_genres')
    if isinstance(favorite_genres, str):
        import json
        try:
            favorite_genres = json.loads(favorite_genres)
        except:
            favorite_genres = []
    
    return UserResponse(
        user_id=user['user_id'],
        username=user['username'],
        email=user['email'],
        created_at=str(user.get('created_at', '')),
        favorite_mood=user.get('favorite_mood'),
        favorite_genres=favorite_genres or []
    )
