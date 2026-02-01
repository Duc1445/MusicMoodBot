"""
Authentication API Routes for MusicMoodBot
===========================================
Provides JWT-based authentication endpoints:
- POST /auth/login - Login and get tokens
- POST /auth/signup - Register new user
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout and revoke tokens
- GET /auth/me - Get current user info
- POST /auth/change-password - Change password

Author: MusicMoodBot Team
Version: 1.0.0
"""

import os
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, validator

from .jwt_auth import (
    LoginRequest,
    SignupRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    TokenResponse,
    UserResponse,
    create_token_pair,
    decode_token,
    revoke_token,
    verify_password,
    create_password_hash,
    get_current_user,
    jwt_config
)

# Database imports
from backend.src.database.database import get_user, add_user, DB_PATH


# ==================== ROUTER ====================

router = APIRouter(prefix="/auth", tags=["authentication"])


# ==================== HELPER FUNCTIONS ====================

def get_db_path() -> str:
    """Get absolute path to music.db"""
    current_file = os.path.abspath(__file__)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    return os.path.join(backend_dir, "src", "database", "music.db")


def get_user_by_id(user_id: int) -> Dict[str, Any]:
    """Get user by ID from database"""
    import sqlite3
    
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT user_id, username, email, created_at FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def update_user_password(user_id: int, new_password_hash: str) -> bool:
    """Update user password in database"""
    import sqlite3
    
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # Try password_hash column first, then password
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE user_id = ?",
            (new_password_hash, user_id)
        )
        
        if cursor.rowcount == 0:
            cursor.execute(
                "UPDATE users SET password = ? WHERE user_id = ?",
                (new_password_hash, user_id)
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        return False


# ==================== ENDPOINTS ====================

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT tokens.
    
    Request body:
        - email: User email or username
        - password: User password
        
    Returns:
        - access_token: JWT access token
        - refresh_token: JWT refresh token
        - token_type: "Bearer"
        - expires_in: Token expiration in seconds
        - user: User information
    """
    # Get user from database
    user = get_user(request.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác"
        )
    
    # Verify password
    stored_password = user.get("password_hash", user.get("password", ""))
    
    if not verify_password(request.password, stored_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác"
        )
    
    # Create token pair
    user_id = user.get("user_id")
    email = user.get("email", request.email)
    name = user.get("username", "User")
    
    return create_token_pair(user_id, email, name)


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """
    Register a new user and return JWT tokens.
    
    Request body:
        - name: User's display name
        - email: User email (unique)
        - password: User password (min 6 characters)
        
    Returns:
        - access_token: JWT access token
        - refresh_token: JWT refresh token
        - token_type: "Bearer"
        - expires_in: Token expiration in seconds
        - user: User information
    """
    # Validate password length
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu phải có ít nhất 6 ký tự"
        )
    
    # Check if user exists
    existing_user = get_user(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã tồn tại"
        )
    
    # Hash password
    password_hash = create_password_hash(request.password)
    
    # Add user to database
    user_id = add_user(request.name, request.email, password_hash)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo tài khoản. Vui lòng thử lại"
        )
    
    # Create token pair
    return create_token_pair(user_id, request.email, request.name)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    Request body:
        - refresh_token: Valid refresh token
        
    Returns:
        New token pair
    """
    # Decode and verify refresh token
    payload = decode_token(request.refresh_token, verify_type=jwt_config.TOKEN_TYPE_REFRESH)
    
    user_id = int(payload.get("sub"))
    
    # Get user info from database
    user = get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Revoke old refresh token
    revoke_token(request.refresh_token)
    
    # Create new token pair
    return create_token_pair(
        user_id,
        user.get("email"),
        user.get("username", "User")
    )


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Logout user and revoke tokens.
    
    Requires: Bearer token in Authorization header
    
    Returns:
        Success message
    """
    # In a real implementation, we would also revoke the access token
    # For now, just return success (client should discard tokens)
    return {"message": "Đăng xuất thành công", "success": True}


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """
    Get current authenticated user info.
    
    Requires: Bearer token in Authorization header
    
    Returns:
        User information
    """
    # Get fresh user data from database
    user_data = get_user_by_id(user["user_id"])
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        user_id=user_data.get("user_id"),
        name=user_data.get("username", "User"),
        email=user_data.get("email", ""),
        created_at=user_data.get("created_at")
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: dict = Depends(get_current_user)
):
    """
    Change user password.
    
    Requires: Bearer token in Authorization header
    
    Request body:
        - old_password: Current password
        - new_password: New password (min 6 characters)
        
    Returns:
        Success message
    """
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu mới phải có ít nhất 6 ký tự"
        )
    
    # Get user from database with password
    import sqlite3
    
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user["user_id"],)
    )
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_dict = dict(user_data)
    
    # Verify old password
    stored_password = user_dict.get("password_hash", user_dict.get("password", ""))
    
    if not verify_password(request.old_password, stored_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mật khẩu cũ không chính xác"
        )
    
    # Hash and update new password
    new_password_hash = create_password_hash(request.new_password)
    
    if not update_user_password(user["user_id"], new_password_hash):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể đổi mật khẩu. Vui lòng thử lại"
        )
    
    return {"message": "Đổi mật khẩu thành công", "success": True}


@router.get("/verify")
async def verify_token(user: dict = Depends(get_current_user)):
    """
    Verify if token is valid.
    
    Requires: Bearer token in Authorization header
    
    Returns:
        Token validity status
    """
    return {
        "valid": True,
        "user_id": user["user_id"],
        "email": user.get("email"),
        "name": user.get("name")
    }
