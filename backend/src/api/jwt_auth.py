"""
JWT Authentication Module for MusicMoodBot Backend
====================================================
Provides JWT token generation, validation, and middleware.

Features:
- Access & Refresh token pair
- Token blacklisting for logout
- Secure password verification
- Role-based access (future)

Author: MusicMoodBot Team
Version: 1.0.0
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# JWT library
try:
    import jwt
    HAS_JWT = True
except ImportError:
    # Fallback to PyJWT
    try:
        import jose.jwt as jwt
        from jose import JWTError
        HAS_JWT = True
    except ImportError:
        HAS_JWT = False
        print("WARNING: JWT library not installed. Run: pip install PyJWT")


# ==================== CONFIGURATION ====================

class JWTConfig:
    """JWT Configuration"""
    
    # Secret key for signing tokens (should be in .env in production)
    SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", 
        "mmb_super_secret_key_change_in_production_" + secrets.token_hex(16)
    )
    
    # Algorithm for token signing
    ALGORITHM = "HS256"
    
    # Token expiration times (in minutes)
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 days
    
    # Token types
    TOKEN_TYPE_ACCESS = "access"
    TOKEN_TYPE_REFRESH = "refresh"


# Global config
jwt_config = JWTConfig()


# ==================== PYDANTIC MODELS ====================

class TokenPayload(BaseModel):
    """JWT Token payload"""
    sub: str  # Subject (user_id)
    exp: datetime
    iat: datetime
    type: str  # access or refresh
    email: Optional[str] = None
    name: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds
    user: Dict[str, Any]


class LoginRequest(BaseModel):
    """Login request model"""
    email: str
    password: str


class SignupRequest(BaseModel):
    """Signup request model"""
    name: str
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    old_password: str
    new_password: str


class UserResponse(BaseModel):
    """User response model"""
    user_id: int
    name: str
    email: str
    created_at: Optional[str] = None


# ==================== TOKEN BLACKLIST ====================

class TokenBlacklist:
    """
    In-memory token blacklist for invalidated tokens.
    
    In production, use Redis or database for persistence.
    """
    
    def __init__(self):
        self._blacklist: set = set()
        self._cleanup_interval = timedelta(hours=1)
        self._last_cleanup = datetime.now()
    
    def add(self, token_jti: str, expires_at: datetime):
        """Add token to blacklist"""
        self._blacklist.add((token_jti, expires_at))
        self._cleanup_if_needed()
    
    def is_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted"""
        self._cleanup_if_needed()
        return any(jti == token_jti for jti, _ in self._blacklist)
    
    def _cleanup_if_needed(self):
        """Remove expired tokens from blacklist"""
        now = datetime.now()
        if now - self._last_cleanup > self._cleanup_interval:
            self._blacklist = {
                (jti, exp) for jti, exp in self._blacklist 
                if exp > now
            }
            self._last_cleanup = now


# Global blacklist
token_blacklist = TokenBlacklist()


# ==================== PASSWORD UTILITIES ====================

def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """
    Hash password using SHA-256 with salt.
    
    Returns: (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    salted = f"{password}{salt}"
    hashed = hashlib.sha256(salted.encode('utf-8')).hexdigest()
    
    return hashed, salt


def verify_password(password: str, stored_password: str) -> bool:
    """
    Verify password against stored hash.
    
    Supports format: "hash:salt" or plain text (legacy)
    """
    if ":" in stored_password:
        stored_hash, salt = stored_password.split(":", 1)
        computed_hash, _ = hash_password(password, salt)
        return secrets.compare_digest(computed_hash, stored_hash)
    else:
        # Legacy plain text comparison
        return stored_password == password


def create_password_hash(password: str) -> str:
    """Create password hash for storage"""
    hashed, salt = hash_password(password)
    return f"{hashed}:{salt}"


# ==================== TOKEN UTILITIES ====================

def create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Dict[str, Any] = None
) -> str:
    """
    Create a JWT token.
    
    Args:
        subject: Token subject (usually user_id)
        token_type: "access" or "refresh"
        expires_delta: Token expiration time
        extra_claims: Additional claims to include
        
    Returns:
        Encoded JWT token
    """
    if not HAS_JWT:
        raise RuntimeError("JWT library not installed")
    
    now = datetime.utcnow()
    expire = now + expires_delta
    
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": expire,
        "jti": secrets.token_hex(16),  # Unique token ID
    }
    
    if extra_claims:
        payload.update(extra_claims)
    
    return jwt.encode(payload, jwt_config.SECRET_KEY, algorithm=jwt_config.ALGORITHM)


def create_access_token(user_id: int, email: str = None, name: str = None) -> str:
    """Create access token for user"""
    expires_delta = timedelta(minutes=jwt_config.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(
        subject=str(user_id),
        token_type=jwt_config.TOKEN_TYPE_ACCESS,
        expires_delta=expires_delta,
        extra_claims={"email": email, "name": name}
    )


def create_refresh_token(user_id: int) -> str:
    """Create refresh token for user"""
    expires_delta = timedelta(days=jwt_config.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(
        subject=str(user_id),
        token_type=jwt_config.TOKEN_TYPE_REFRESH,
        expires_delta=expires_delta
    )


def create_token_pair(user_id: int, email: str = None, name: str = None) -> TokenResponse:
    """
    Create access and refresh token pair.
    
    Returns:
        TokenResponse with both tokens
    """
    access_token = create_access_token(user_id, email, name)
    refresh_token = create_refresh_token(user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=jwt_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "user_id": user_id,
            "email": email,
            "name": name
        }
    )


def decode_token(token: str, verify_type: str = None) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: The JWT token to decode
        verify_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException if token is invalid
    """
    if not HAS_JWT:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT library not installed"
        )
    
    try:
        payload = jwt.decode(
            token,
            jwt_config.SECRET_KEY,
            algorithms=[jwt_config.ALGORITHM]
        )
        
        # Check token type if specified
        if verify_type and payload.get("type") != verify_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {verify_type}"
            )
        
        # Check blacklist
        jti = payload.get("jti")
        if jti and token_blacklist.is_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


def revoke_token(token: str):
    """
    Revoke a token by adding it to blacklist.
    """
    try:
        # Decode without verification to get expiry
        payload = jwt.decode(
            token,
            jwt_config.SECRET_KEY,
            algorithms=[jwt_config.ALGORITHM],
            options={"verify_exp": False}
        )
        jti = payload.get("jti")
        exp = datetime.fromtimestamp(payload.get("exp", 0))
        
        if jti:
            token_blacklist.add(jti, exp)
    except Exception:
        pass  # Token already invalid


# ==================== FASTAPI DEPENDENCIES ====================

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"message": f"Hello {user['name']}"}
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = decode_token(token, verify_type=jwt_config.TOKEN_TYPE_ACCESS)
    
    return {
        "user_id": int(payload.get("sub")),
        "email": payload.get("email"),
        "name": payload.get("name")
    }


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns None if not authenticated.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# ==================== EXPORTS ====================

__all__ = [
    # Config
    'jwt_config',
    'JWTConfig',
    
    # Models
    'TokenPayload',
    'TokenResponse',
    'LoginRequest',
    'SignupRequest',
    'RefreshTokenRequest',
    'ChangePasswordRequest',
    'UserResponse',
    
    # Password utilities
    'hash_password',
    'verify_password',
    'create_password_hash',
    
    # Token utilities
    'create_token',
    'create_access_token',
    'create_refresh_token',
    'create_token_pair',
    'decode_token',
    'revoke_token',
    
    # FastAPI dependencies
    'security',
    'get_current_user',
    'get_current_user_optional',
    
    # Blacklist
    'token_blacklist'
]
